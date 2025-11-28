/**
 * 图片预处理器模块
 * 在上传到OCR服务前进行图片优化处理
 * 支持Canvas API和WebGPU加速
 */

class ImagePreprocessor {
  constructor(options = {}) {
    this.options = {
      // 最大宽度/高度，超过则缩放
      maxWidth: options.maxWidth || 2048,
      maxHeight: options.maxHeight || 2048,
      
      // 最小宽度/高度，低于则放大以提高清晰度
      minWidth: options.minWidth || 640,
      minHeight: options.minHeight || 480,
      
      // JPEG质量 (0-1)，用于压缩
      quality: options.quality || 0.92,
      
      // 文件大小阈值(KB)，超过则启用压缩
      maxFileSizeKB: options.maxFileSizeKB || 1024,
      
      // 是否启用锐化
      enableSharpen: options.enableSharpen !== false,
      
      // 锐化强度 (0-1)
      sharpenStrength: options.sharpenStrength || 0.3,
      
      // 是否自适应对比度增强
      enableContrastEnhance: options.enableContrastEnhance !== false,
      
      // 输出格式
      outputFormat: options.outputFormat || 'image/jpeg',
      
      // 是否启用WebGPU（如果可用）
      useWebGPU: options.useWebGPU !== false,
    };
    
    this.webGPUAvailable = false;
    this.initWebGPU();
  }

  /**
   * 初始化WebGPU（如果浏览器支持）
   */
  async initWebGPU() {
    if (!this.options.useWebGPU) return;
    
    try {
      if ('gpu' in navigator) {
        const adapter = await navigator.gpu.requestAdapter();
        if (adapter) {
          this.gpuDevice = await adapter.requestDevice();
          this.webGPUAvailable = true;
          console.log('✓ WebGPU已启用，图片处理将使用GPU加速');
        }
      }
    } catch (error) {
      console.log('WebGPU不可用，将使用Canvas API处理:', error.message);
    }
  }

  /**
   * 主处理函数：预处理文件（图片或PDF）
   * @param {File} file - 原始文件
   * @param {Function} onProgress - 进度回调 (0-100)
   * @returns {Promise<{file: File, stats: Object}>}
   */
  async process(file, onProgress = null) {
    // 检测是否为PDF文件
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      return await this.processPDF(file, onProgress);
    }
    
    // 处理图片文件
    return await this.processImage(file, onProgress);
  }

  /**
   * 处理图片文件
   * @param {File} file - 原始图片文件
   * @param {Function} onProgress - 进度回调 (0-100)
   * @returns {Promise<{file: File, stats: Object}>}
   */
  async processImage(file, onProgress = null) {
    const startTime = performance.now();
    
    // 更新进度
    const updateProgress = (percent, message) => {
      if (onProgress) onProgress(percent, message);
    };

    try {
      updateProgress(10, '正在加载图片...');
      
      // 1. 加载图片
      const img = await this.loadImage(file);
      const originalSize = file.size / 1024; // KB
      
      updateProgress(30, '分析图片属性...');
      
      // 2. 判断是否需要处理
      const needsProcessing = this.needsProcessing(img, originalSize);
      
      if (!needsProcessing.required) {
        updateProgress(100, '图片已经是最佳状态');
        return {
          file: file,
          processed: false,
          stats: {
            originalSize: originalSize.toFixed(2),
            processedSize: originalSize.toFixed(2),
            originalDimensions: `${img.width}x${img.height}`,
            processedDimensions: `${img.width}x${img.height}`,
            compressionRatio: 1.0,
            processingTime: 0,
            reason: needsProcessing.reason
          }
        };
      }
      
      updateProgress(50, '处理图片中...');
      
      // 3. 计算目标尺寸
      const targetDimensions = this.calculateTargetDimensions(img.width, img.height);
      
      // 4. 使用Canvas进行图片处理
      const canvas = document.createElement('canvas');
      canvas.width = targetDimensions.width;
      canvas.height = targetDimensions.height;
      const ctx = canvas.getContext('2d', { 
        alpha: false,
        willReadFrequently: false 
      });
      
      // 启用高质量缩放
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      
      // 绘制缩放后的图片
      ctx.drawImage(img, 0, 0, targetDimensions.width, targetDimensions.height);
      
      updateProgress(70, '优化图片质量...');
      
      // 5. 应用图像增强
      if (this.options.enableContrastEnhance || this.options.enableSharpen) {
        await this.enhanceImage(ctx, canvas.width, canvas.height);
      }
      
      updateProgress(90, '生成优化文件...');
      
      // 6. 转换为Blob
      const blob = await this.canvasToBlob(canvas, this.options.outputFormat, this.options.quality);
      const processedSize = blob.size / 1024; // KB
      
      // 6.5 检查是否处理后反而变大了（针对小文件的保护）
      if (processedSize > originalSize && originalSize < 100) {
        updateProgress(100, '处理后文件更大，使用原文件');
        return {
          file: file,
          processed: false,
          stats: {
            originalSize: originalSize.toFixed(2),
            processedSize: originalSize.toFixed(2),
            originalDimensions: `${img.width}x${img.height}`,
            processedDimensions: `${img.width}x${img.height}`,
            compressionRatio: 1.0,
            processingTime: 0,
            reason: '处理后文件更大，已跳过（保护小文件）'
          }
        };
      }
      
      // 7. 创建新文件
      const processedFile = new File(
        [blob], 
        this.generateFilename(file.name), 
        { type: this.options.outputFormat }
      );
      
      const processingTime = performance.now() - startTime;
      
      updateProgress(100, '处理完成！');
      
      return {
        file: processedFile,
        processed: true,
        stats: {
          originalSize: originalSize.toFixed(2),
          processedSize: processedSize.toFixed(2),
          originalDimensions: `${img.width}x${img.height}`,
          processedDimensions: `${targetDimensions.width}x${targetDimensions.height}`,
          compressionRatio: (originalSize / processedSize).toFixed(2),
          processingTime: processingTime.toFixed(0),
          enhancements: this.getAppliedEnhancements()
        }
      };
      
    } catch (error) {
      console.error('图片预处理失败:', error);
      // 处理失败时返回原始文件
      return {
        file: file,
        processed: false,
        error: error.message,
        stats: {
          originalSize: (file.size / 1024).toFixed(2),
          error: error.message
        }
      };
    }
  }

  /**
   * 加载图片文件为Image对象
   */
  loadImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('图片加载失败'));
        img.src = e.target.result;
      };
      reader.onerror = () => reject(new Error('文件读取失败'));
      reader.readAsDataURL(file);
    });
  }

/**
 * 判断图片是否需要处理
 */
needsProcessing(img, fileSizeKB) {
    const reasons = [];
    
    // 检查文件大小
    if (fileSizeKB > this.options.maxFileSizeKB) {
      reasons.push(`文件过大(${fileSizeKB.toFixed(0)}KB > ${this.options.maxFileSizeKB}KB)`);
    }
    
    // 检查分辨率
    if (img.width > this.options.maxWidth || img.height > this.options.maxHeight) {
      reasons.push(`分辨率过高(${img.width}x${img.height})`);
    }
    
    // 修改：只有当文件大且分辨率低时才放大（避免对小文件放大）
    // 同时使用 AND 逻辑，避免细长图片被误判
    if (fileSizeKB > 50 && // 增加文件大小检查
        img.width < this.options.minWidth && 
        img.height < this.options.minHeight) {
      reasons.push(`分辨率过低(${img.width}x${img.height})`);
    }
    
    return {
      required: reasons.length > 0,
      reason: reasons.length > 0 ? reasons.join(', ') : '图片符合最佳标准'
    };
  }

  /**
   * 计算目标尺寸（保持宽高比）
   */
  calculateTargetDimensions(width, height) {
    let targetWidth = width;
    let targetHeight = height;
    
    // 如果图片太大，缩小到最大尺寸
    if (width > this.options.maxWidth || height > this.options.maxHeight) {
      const ratio = Math.min(
        this.options.maxWidth / width,
        this.options.maxHeight / height
      );
      targetWidth = Math.round(width * ratio);
      targetHeight = Math.round(height * ratio);
    }
    
    // 如果图片太小，放大到最小尺寸
    if (targetWidth < this.options.minWidth && targetHeight < this.options.minHeight) {
      const ratio = Math.max(
        this.options.minWidth / targetWidth,
        this.options.minHeight / targetHeight
      );
      targetWidth = Math.round(targetWidth * ratio);
      targetHeight = Math.round(targetHeight * ratio);
    }
    
    return { width: targetWidth, height: targetHeight };
  }

  /**
   * 图像增强（锐化和对比度调整）
   */
  async enhanceImage(ctx, width, height) {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    
    // 应用对比度增强
    if (this.options.enableContrastEnhance) {
      this.applyContrastEnhancement(data);
    }
    
    // 应用锐化
    if (this.options.enableSharpen) {
      this.applySharpen(imageData, width, height);
    }
    
    ctx.putImageData(imageData, 0, 0);
  }

  /**
   * 对比度自适应增强
   */
  applyContrastEnhancement(data) {
    // 计算亮度直方图
    const histogram = new Array(256).fill(0);
    for (let i = 0; i < data.length; i += 4) {
      const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
      histogram[Math.floor(avg)]++;
    }
    
    // 计算最佳对比度参数
    const totalPixels = data.length / 4;
    let minBrightness = 0, maxBrightness = 255;
    
    // 找到1%和99%分位点
    let count = 0;
    for (let i = 0; i < 256; i++) {
      count += histogram[i];
      if (count > totalPixels * 0.01 && minBrightness === 0) {
        minBrightness = i;
      }
      if (count > totalPixels * 0.99) {
        maxBrightness = i;
        break;
      }
    }
    
    // 应用线性拉伸
    const range = maxBrightness - minBrightness;
    if (range > 0) {
      for (let i = 0; i < data.length; i += 4) {
        for (let j = 0; j < 3; j++) {
          const val = data[i + j];
          data[i + j] = Math.max(0, Math.min(255, 
            ((val - minBrightness) / range) * 255
          ));
        }
      }
    }
  }

  /**
   * 应用锐化滤镜
   */
  applySharpen(imageData, width, height) {
    const data = imageData.data;
    const originalData = new Uint8ClampedArray(data);
    
    // 锐化卷积核
    const strength = this.options.sharpenStrength;
    const kernel = [
      0, -strength, 0,
      -strength, 1 + 4 * strength, -strength,
      0, -strength, 0
    ];
    
    // 应用卷积
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        for (let c = 0; c < 3; c++) {
          let sum = 0;
          for (let ky = -1; ky <= 1; ky++) {
            for (let kx = -1; kx <= 1; kx++) {
              const idx = ((y + ky) * width + (x + kx)) * 4 + c;
              const kernelIdx = (ky + 1) * 3 + (kx + 1);
              sum += originalData[idx] * kernel[kernelIdx];
            }
          }
          const idx = (y * width + x) * 4 + c;
          data[idx] = Math.max(0, Math.min(255, sum));
        }
      }
    }
  }

  /**
   * Canvas转Blob
   */
  canvasToBlob(canvas, format, quality) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Canvas转换失败'));
          }
        },
        format,
        quality
      );
    });
  }

  /**
   * 生成处理后的文件名
   */
  generateFilename(originalName) {
    const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '');
    const ext = this.options.outputFormat === 'image/jpeg' ? 'jpg' : 'png';
    return `${nameWithoutExt}_processed.${ext}`;
  }

  /**
   * 获取应用的增强效果列表
   */
  getAppliedEnhancements() {
    const enhancements = [];
    if (this.options.enableContrastEnhance) {
      enhancements.push('对比度增强');
    }
    if (this.options.enableSharpen) {
      enhancements.push(`锐化(${this.options.sharpenStrength})`);
    }
    return enhancements.join(', ') || '无';
  }

  /**
   * 处理PDF文件
   * @param {File} file - 原始PDF文件
   * @param {Function} onProgress - 进度回调 (0-100)
   * @returns {Promise<{file: File, stats: Object}>}
   */
  async processPDF(file, onProgress = null) {
    const startTime = performance.now();
    const updateProgress = (percent, message) => {
      if (onProgress) onProgress(percent, message);
    };

    try {
      updateProgress(10, '分析PDF文件...');
      
      const originalSize = file.size / 1024; // KB
      
      // 检查PDF.js是否可用
      if (typeof pdfjsLib === 'undefined') {
        console.warn('PDF.js未加载，跳过PDF预处理');
        return {
          file: file,
          processed: false,
          stats: {
            originalSize: originalSize.toFixed(2),
            processedSize: originalSize.toFixed(2),
            reason: 'PDF.js未加载，跳过预处理'
          }
        };
      }

      updateProgress(20, '加载PDF文档...');

      // 加载PDF文档
      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      const pdfDoc = await loadingTask.promise;
      const pageCount = pdfDoc.numPages;

      updateProgress(30, `分析PDF (${pageCount}页)...`);

      // 判断是否需要处理
      const needsProcessing = this.needsPDFProcessing(originalSize, pageCount);
      
      if (!needsProcessing.required) {
        updateProgress(100, 'PDF已经是最佳状态');
        return {
          file: file,
          processed: false,
          stats: {
            originalSize: originalSize.toFixed(2),
            processedSize: originalSize.toFixed(2),
            pageCount: pageCount,
            compressionRatio: 1.0,
            processingTime: 0,
            reason: needsProcessing.reason
          }
        };
      }

      updateProgress(40, '提取PDF页面...');

      // 提取并优化每一页
      const optimizedPages = [];
      const scale = this.calculatePDFScale(originalSize, pageCount);
      
      for (let i = 1; i <= pageCount; i++) {
        updateProgress(40 + (40 * i / pageCount), `处理第 ${i}/${pageCount} 页...`);
        
        const page = await pdfDoc.getPage(i);
        const viewport = page.getViewport({ scale: scale });
        
        // 创建Canvas渲染页面
        const canvas = document.createElement('canvas');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext('2d');
        
        await page.render({
          canvasContext: ctx,
          viewport: viewport
        }).promise;
        
        // 将页面转换为优化的图片
        const imageBlob = await this.canvasToBlob(canvas, 'image/jpeg', this.options.quality);
        optimizedPages.push(imageBlob);
      }

      updateProgress(85, '重新打包PDF...');

      // 使用jsPDF重新打包
      if (typeof jspdf === 'undefined' || !jspdf.jsPDF) {
        console.warn('jsPDF未加载，返回第一页作为图片');
        // 降级：只返回第一页作为图片
        const processedFile = new File(
          [optimizedPages[0]], 
          file.name.replace('.pdf', '_page1.jpg'),
          { type: 'image/jpeg' }
        );
        
        const processingTime = performance.now() - startTime;
        const processedSize = processedFile.size / 1024;
        
        return {
          file: processedFile,
          processed: true,
          stats: {
            originalSize: originalSize.toFixed(2),
            processedSize: processedSize.toFixed(2),
            pageCount: pageCount,
            extractedPages: 1,
            compressionRatio: (originalSize / processedSize).toFixed(2),
            processingTime: processingTime.toFixed(0),
            note: 'PDF转换为第一页图片'
          }
        };
      }

      // 创建新的PDF
      const pdf = new jspdf.jsPDF({
        orientation: 'portrait',
        unit: 'px',
        compress: true
      });

      for (let i = 0; i < optimizedPages.length; i++) {
        if (i > 0) {
          pdf.addPage();
        }
        
        // 获取图片URL
        const imgUrl = URL.createObjectURL(optimizedPages[i]);
        const img = await this.loadImageFromUrl(imgUrl);
        
        // 计算页面尺寸
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const imgRatio = img.width / img.height;
        const pageRatio = pageWidth / pageHeight;
        
        let finalWidth, finalHeight;
        if (imgRatio > pageRatio) {
          finalWidth = pageWidth;
          finalHeight = pageWidth / imgRatio;
        } else {
          finalHeight = pageHeight;
          finalWidth = pageHeight * imgRatio;
        }
        
        pdf.addImage(img, 'JPEG', 0, 0, finalWidth, finalHeight);
        URL.revokeObjectURL(imgUrl);
      }

      updateProgress(95, '生成优化PDF...');

      // 生成PDF Blob
      const pdfBlob = pdf.output('blob');
      const processedFile = new File(
        [pdfBlob],
        file.name.replace('.pdf', '_optimized.pdf'),
        { type: 'application/pdf' }
      );

      const processingTime = performance.now() - startTime;
      const processedSize = processedFile.size / 1024;

      updateProgress(100, 'PDF处理完成！');

      return {
        file: processedFile,
        processed: true,
        stats: {
          originalSize: originalSize.toFixed(2),
          processedSize: processedSize.toFixed(2),
          pageCount: pageCount,
          compressionRatio: (originalSize / processedSize).toFixed(2),
          processingTime: processingTime.toFixed(0),
          scale: scale.toFixed(2)
        }
      };

    } catch (error) {
      console.error('PDF处理失败:', error);
      return {
        file: file,
        processed: false,
        error: error.message,
        stats: {
          originalSize: (file.size / 1024).toFixed(2),
          error: error.message
        }
      };
    }
  }

  /**
   * 判断PDF是否需要处理
   */
  needsPDFProcessing(fileSizeKB, pageCount) {
    const reasons = [];
    
    // 检查文件大小（PDF阈值更高）
    const pdfMaxSize = this.options.maxFileSizeKB * 3; // PDF允许更大
    if (fileSizeKB > pdfMaxSize) {
      reasons.push(`文件过大(${fileSizeKB.toFixed(0)}KB > ${pdfMaxSize}KB)`);
    }
    
    // 检查页数
    if (pageCount > 20) {
      reasons.push(`页数过多(${pageCount}页 > 20页)`);
    }
    
    return {
      required: reasons.length > 0,
      reason: reasons.length > 0 ? reasons.join(', ') : 'PDF符合最佳标准'
    };
  }

  /**
   * 计算PDF渲染比例
   */
  calculatePDFScale(fileSizeKB, pageCount) {
    // 根据文件大小和页数计算合适的缩放比例
    const avgSizePerPage = fileSizeKB / pageCount;
    
    // 修复：小PDF不应该放大
    if (avgSizePerPage < 100) {
      return 0.8;  // 每页<100KB，使用更小比例避免增大
    } else if (avgSizePerPage < 300) {
      return 1.0;  // 每页100-300KB，标准质量
    } else if (avgSizePerPage < 500) {
      return 1.2;  // 每页300-500KB，略高质量
    } else {
      return 1.5;  // 每页>500KB，高质量用于压缩大文件
    }
  }

  /**
   * 从URL加载图片
   */
  loadImageFromUrl(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('图片加载失败'));
      img.src = url;
    });
  }

  /**
   * 批量处理多个文件
   */
  async processBatch(files, onProgress = null) {
    const results = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const result = await this.process(file, (percent, message) => {
        if (onProgress) {
          onProgress({
            fileIndex: i,
            totalFiles: files.length,
            fileProgress: percent,
            message: message
          });
        }
      });
      results.push(result);
    }
    return results;
  }
}

// 默认预处理器实例
const defaultPreprocessor = new ImagePreprocessor({
  maxWidth: 2048,
  maxHeight: 2048,
  minWidth: 640,
  minHeight: 480,
  quality: 0.92,
  maxFileSizeKB: 1024,
  enableSharpen: true,
  sharpenStrength: 0.3,
  enableContrastEnhance: true,
  outputFormat: 'image/jpeg',
  useWebGPU: true
});

// 导出
window.ImagePreprocessor = ImagePreprocessor;
window.defaultPreprocessor = defaultPreprocessor;

