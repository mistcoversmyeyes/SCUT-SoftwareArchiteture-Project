const API_BASE = "http://localhost:8090/api/v1";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

// 图片预处理器配置
let preprocessorEnabled = true;
let currentPreprocessor = null;

const formatSeconds = (value) =>
  typeof value === "number" ? `${value.toFixed(3)}s` : "—";

const escapeHtml = (unsafe = "") =>
  unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

const stringify = (payload) => escapeHtml(JSON.stringify(payload ?? {}, null, 2));

const setResult = (id, { html, mode = "neutral" }) => {
  const container = document.getElementById(id);
  container.classList.remove("error", "success");
  if (mode === "error") container.classList.add("error");
  if (mode === "success") container.classList.add("success");
  container.innerHTML = html;
};

const setLoadingState = (form, isLoading) => {
  const submitBtn = form.querySelector("button[type='submit']");
  if (!submitBtn) return;
  if (!submitBtn.dataset.defaultLabel) {
    submitBtn.dataset.defaultLabel = submitBtn.textContent;
  }
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "处理中..." : submitBtn.dataset.defaultLabel;
};

const ensureFileSelected = (inputEl, resultContainerId) => {
  if (!inputEl.files.length) {
    setResult(resultContainerId, {
      html: "<div><strong>提示：</strong>请先选择待识别文件。</div>",
      mode: "error",
    });
    return false;
  }
  return true;
};

/**
 * 预处理图片文件
 * @param {File} file - 原始文件
 * @param {string} resultContainerId - 结果容器ID
 * @returns {Promise<{file: File, stats: Object}>}
 */
const preprocessFile = async (file, resultContainerId) => {
  // 检查文件类型：支持图片和PDF
  const isImage = file.type.startsWith('image/');
  const isPDF = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  
  if (!isImage && !isPDF) {
    return {
      file: file,
      processed: false,
      stats: {
        originalSize: (file.size / 1024).toFixed(2),
        reason: '不支持的文件类型，跳过预处理'
      }
    };
  }

  // 如果预处理器未启用，直接返回
  if (!preprocessorEnabled) {
    return {
      file: file,
      processed: false,
      stats: {
        originalSize: (file.size / 1024).toFixed(2),
        reason: '预处理器已禁用'
      }
    };
  }

  try {
    // 显示处理进度
    const fileTypeName = isPDF ? 'PDF' : '图片';
    setResult(resultContainerId, {
      html: `<div class="preprocessing-status"><strong>正在预处理${fileTypeName}...</strong><div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div><div class="progress-text">准备中...</div></div>`,
      mode: "neutral"
    });

    const progressFill = document.querySelector(`#${resultContainerId} .progress-fill`);
    const progressText = document.querySelector(`#${resultContainerId} .progress-text`);

    // 使用全局预处理器实例
    if (!currentPreprocessor && window.defaultPreprocessor) {
      currentPreprocessor = window.defaultPreprocessor;
    }

    if (!currentPreprocessor) {
      throw new Error('预处理器未初始化');
    }

    // 执行预处理
    const result = await currentPreprocessor.process(file, (percent, message) => {
      if (progressFill) {
        progressFill.style.width = `${percent}%`;
      }
      if (progressText) {
        progressText.textContent = message;
      }
    });

    // 显示预处理统计
    if (result.processed) {
      const stats = result.stats;
      let statsHtml = `
        <div class="preprocessing-success">
          <strong>✓ ${isPDF ? 'PDF' : '图片'}预处理完成</strong>
          <div class="stats-grid">
            <div>原始大小: ${stats.originalSize}KB</div>
            <div>处理后: ${stats.processedSize}KB</div>`;
      
      // PDF特有的统计
      if (stats.pageCount) {
        statsHtml += `<div>页数: ${stats.pageCount}页</div>`;
      }
      if (stats.extractedPages) {
        statsHtml += `<div>提取页数: ${stats.extractedPages}页</div>`;
      }
      
      // 图片特有的统计
      if (stats.originalDimensions) {
        statsHtml += `
            <div>原始尺寸: ${stats.originalDimensions}</div>
            <div>处理后: ${stats.processedDimensions}</div>`;
      }
      
      statsHtml += `
            <div>压缩比: ${stats.compressionRatio}x</div>
            <div>处理时间: ${stats.processingTime}ms</div>`;
      
      if (stats.enhancements) {
        statsHtml += `<div>应用增强: ${stats.enhancements}</div>`;
      }
      if (stats.scale) {
        statsHtml += `<div>渲染比例: ${stats.scale}</div>`;
      }
      if (stats.note) {
        statsHtml += `<div class="note">${stats.note}</div>`;
      }
      
      statsHtml += `
          </div>
        </div>`;
      
      setResult(resultContainerId, {
        html: statsHtml,
        mode: "success"
      });
    } else {
      setResult(resultContainerId, {
        html: `<div><strong>ℹ</strong> ${result.stats.reason || '文件无需处理'}</div>`,
        mode: "neutral"
      });
    }

    return result;
  } catch (error) {
    console.error('预处理失败:', error);
    setResult(resultContainerId, {
      html: `<div><strong>⚠ 预处理失败:</strong> ${escapeHtml(error.message)}<br>将使用原始文件继续...</div>`,
      mode: "error"
    });
    return {
      file: file,
      processed: false,
      error: error.message
    };
  }
};

const appendBooleanField = (formData, key, value) => {
  formData.append(key, value ? "true" : "false");
};

const handleFetchError = async (response) => {
  let message = `请求失败：HTTP ${response.status}`;
  let body;

  try {
    body = await response.json();
    if (body?.detail) message = body.detail;
    else if (body?.error) message = body.error;
  } catch (err) {
    // ignore parse error
  }

  const error = new Error(message);
  error.payload = body;
  error.status = response.status;
  throw error;
};

const postFormData = async (endpoint, formData) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    await handleFetchError(response);
  }
  return response.json();
};

const getJson = async (endpoint) => {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    await handleFetchError(response);
  }
  return response.json();
};

const renderOcrSuccess = (containerId, data) => {
  const { pipeline, metrics, result, preprocessing } = data;
  const parts = [];

  parts.push(`<div><strong>Pipeline：</strong>${pipeline}</div>`);

  // 显示预处理信息（如果有）
  if (preprocessing && preprocessing.processedSize) {
    parts.push(
      [
        "<div class='preprocessing-info'><strong>🎨 预处理：</strong>",
        `${preprocessing.originalSize}KB → ${preprocessing.processedSize}KB`,
        ` (${preprocessing.compressionRatio}x) · `,
        `${preprocessing.originalDimensions} → ${preprocessing.processedDimensions}`,
        ` · ${preprocessing.processingTime}ms`,
        preprocessing.enhancements ? ` · ${preprocessing.enhancements}` : "",
        "</div>",
      ].join("")
    );
  }

  if (metrics) {
    parts.push(
      [
        "<div><strong>⏱️ 耗时：</strong>",
        `总耗时 ${formatSeconds(metrics.total_time)} · `,
        `推理 ${formatSeconds(metrics.inference_time)} · `,
        `上传 ${formatSeconds(metrics.upload_time)} · `,
        `尺寸 ${metrics.image_size_kb?.toFixed?.(2) ?? "—"}KB`,
        "</div>",
      ].join("")
    );
    if (typeof metrics.compressed === "boolean") {
      parts.push(`<div>压缩：${metrics.compressed ? "true" : "false"} | 来源：${metrics.source ?? "未知"}</div>`);
    }
  }

  if (result) {
    if (result.text) {
      parts.push(`<h4>识别文本</h4><pre>${escapeHtml(result.text)}</pre>`);
    }
    if (result.markdown) {
      parts.push(`<h4>Markdown</h4><pre>${escapeHtml(result.markdown)}</pre>`);
    }
    if (result.layout || result.tables || result.formulas || result.regions) {
      parts.push(`<details open><summary>结构化结果</summary><pre>${stringify(result)}</pre></details>`);
    } else if (!result.text && !result.markdown) {
      parts.push(`<details open><summary>结果</summary><pre>${stringify(result)}</pre></details>`);
    }
  }

  parts.push(`<details><summary>完整响应</summary><pre>${stringify(data)}</pre></details>`);

  setResult(containerId, { html: parts.join("\n"), mode: "success" });
};

const renderError = (containerId, error) => {
  const extra = error.payload ? `<details><summary>错误响应</summary><pre>${stringify(error.payload)}</pre></details>` : "";
  setResult(containerId, {
    html: `<div><strong>错误：</strong>${escapeHtml(error.message)}</div>${extra}`,
    mode: "error",
  });
};

const bindOcrForms = () => {
  const ocrv5Form = $("#ocrv5-form");
  ocrv5Form.querySelector("button[type='submit']").dataset.defaultLabel = "开始识别";
  ocrv5Form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const fileInput = $("#ocrv5-file");
    if (!ensureFileSelected(fileInput, "ocrv5-result")) return;
    
    setLoadingState(ocrv5Form, true);
    
    try {
      // 预处理图片
      const preprocessResult = await preprocessFile(fileInput.files[0], "ocrv5-result");
      
      // 等待一下让用户看到预处理结果
      if (preprocessResult.processed) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // 构造表单数据
      const formData = new FormData();
      formData.append("file", preprocessResult.file);
      appendBooleanField(formData, "compress", preprocessResult.processed || $("#ocrv5-compress").checked);
      
      // 发送OCR请求
      const data = await postFormData("/text", formData);
      
      // 如果有预处理统计，添加到返回数据中
      if (preprocessResult.stats) {
        data.preprocessing = preprocessResult.stats;
      }
      
      renderOcrSuccess("ocrv5-result", data);
    } catch (error) {
      renderError("ocrv5-result", error);
    } finally {
      setLoadingState(ocrv5Form, false);
    }
  });

  const vlForm = $("#vl-form");
  vlForm.querySelector("button[type='submit']").dataset.defaultLabel = "开始解析";
  vlForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const fileInput = $("#vl-file");
    if (!ensureFileSelected(fileInput, "vl-result")) return;
    
    setLoadingState(vlForm, true);
    
    try {
      // 预处理图片
      const preprocessResult = await preprocessFile(fileInput.files[0], "vl-result");
      
      // 等待一下让用户看到预处理结果
      if (preprocessResult.processed) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // 构造表单数据
      const formData = new FormData();
      formData.append("file", preprocessResult.file);
      appendBooleanField(formData, "compress", preprocessResult.processed || $("#vl-compress").checked);
      formData.append("format", $("#vl-format").value);
      
      // 发送VL请求
      const data = await postFormData("/document/vl_model", formData);
      
      // 如果有预处理统计，添加到返回数据中
      if (preprocessResult.stats) {
        data.preprocessing = preprocessResult.stats;
      }
      
      renderOcrSuccess("vl-result", data);
    } catch (error) {
      renderError("vl-result", error);
    } finally {
      setLoadingState(vlForm, false);
    }
  });

  const structureForm = $("#structure-form");
  structureForm.querySelector("button[type='submit']").dataset.defaultLabel = "开始解析";
  structureForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const fileInput = $("#structure-file");
    if (!ensureFileSelected(fileInput, "structure-result")) return;
    
    setLoadingState(structureForm, true);
    
    try {
      // 预处理图片
      const preprocessResult = await preprocessFile(fileInput.files[0], "structure-result");
      
      // 等待一下让用户看到预处理结果
      if (preprocessResult.processed) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // 构造表单数据
      const formData = new FormData();
      formData.append("file", preprocessResult.file);
      appendBooleanField(formData, "compress", preprocessResult.processed || $("#structure-compress").checked);
      formData.append("output_format", $("#structure-format").value);
      
      // 发送Structure请求
      const data = await postFormData("/document/structure_model", formData);
      
      // 如果有预处理统计，添加到返回数据中
      if (preprocessResult.stats) {
        data.preprocessing = preprocessResult.stats;
      }
      
      renderOcrSuccess("structure-result", data);
    } catch (error) {
      renderError("structure-result", error);
    } finally {
      setLoadingState(structureForm, false);
    }
  });
};

const setGlobalStatus = (status, type = "neutral") => {
  const el = $("#global-status");
  el.textContent = status;
  el.classList.remove("error", "success");
  if (type === "error") el.classList.add("error");
  if (type === "success") el.classList.add("success");
};

const bindMonitorButtons = () => {
  $("#health-btn").addEventListener("click", async () => {
    const btn = $("#health-btn");
    btn.disabled = true;
    btn.textContent = "检测中...";
    try {
      const data = await getJson("/health");
      const pipelineStatus = Object.entries(data.pipelines || {})
        .map(([name, info]) => `${name}: ${info.status ?? "unknown"}`)
        .join("\n");
      setResult("health-result", {
        html: `<div><strong>整体状态：</strong>${data.status}</div><div><strong>时间：</strong>${data.timestamp}</div><pre>${stringify(data.pipelines)}</pre>`,
      });
      setGlobalStatus(`健康状态：${data.status}`, data.status === "healthy" ? "success" : data.status === "degraded" ? "neutral" : "error");
      console.info(pipelineStatus);
    } catch (error) {
      renderError("health-result", error);
      setGlobalStatus("健康检查失败", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "检查健康状态";
    }
  });

  $("#metrics-btn").addEventListener("click", async () => {
    const btn = $("#metrics-btn");
    btn.disabled = true;
    btn.textContent = "拉取中...";
    try {
      const data = await getJson("/metrics");
      const summary = [];
      if (data.total_requests !== undefined) {
        summary.push(`<div><strong>总请求数：</strong>${data.total_requests}</div>`);
      }
      if (data.requests_by_pipeline) {
        summary.push(`<div><strong>产线请求：</strong><pre>${stringify(data.requests_by_pipeline)}</pre></div>`);
      }
      summary.push(`<details open><summary>完整响应</summary><pre>${stringify(data)}</pre></details>`);
      setResult("metrics-result", { html: summary.join("\n") });
    } catch (error) {
      renderError("metrics-result", error);
    } finally {
      btn.disabled = false;
      btn.textContent = "获取性能指标";
    }
  });
};

/**
 * 初始化预处理器设置UI
 */
const initPreprocessorSettings = () => {
  // 创建预处理器设置面板（如果不存在）
  const settingsPanel = document.getElementById('preprocessor-settings');
  if (settingsPanel) {
    // 切换预处理器开关
    const toggleSwitch = document.getElementById('preprocessor-toggle');
    if (toggleSwitch) {
      toggleSwitch.checked = preprocessorEnabled;
      toggleSwitch.addEventListener('change', (e) => {
        preprocessorEnabled = e.target.checked;
        console.log('预处理器已', preprocessorEnabled ? '启用' : '禁用');
        
        // 更新全局状态显示
        const statusEl = document.getElementById('preprocessor-status');
        if (statusEl) {
          statusEl.textContent = preprocessorEnabled ? '已启用' : '已禁用';
          statusEl.className = preprocessorEnabled ? 'status-enabled' : 'status-disabled';
        }
      });
    }

    // 高级设置
    const applySettingsBtn = document.getElementById('apply-preprocessor-settings');
    if (applySettingsBtn) {
      applySettingsBtn.addEventListener('click', () => {
        const maxWidth = parseInt(document.getElementById('max-width')?.value || 2048);
        const maxHeight = parseInt(document.getElementById('max-height')?.value || 2048);
        const quality = parseFloat(document.getElementById('quality')?.value || 0.92);
        const maxFileSize = parseInt(document.getElementById('max-file-size')?.value || 1024);
        const enableSharpen = document.getElementById('enable-sharpen')?.checked ?? true;
        const enableContrast = document.getElementById('enable-contrast')?.checked ?? true;

        // 创建新的预处理器实例
        currentPreprocessor = new window.ImagePreprocessor({
          maxWidth,
          maxHeight,
          quality,
          maxFileSizeKB: maxFileSize,
          enableSharpen,
          enableContrastEnhance: enableContrast,
          outputFormat: 'image/jpeg',
          useWebGPU: true
        });

        console.log('预处理器设置已更新:', {
          maxWidth, maxHeight, quality, maxFileSize, enableSharpen, enableContrast
        });

        alert('预处理器设置已更新！');
      });
    }
  }
};

const init = () => {
  console.log('初始化OCR客户端...');
  
  // 检查是否已加载预处理器
  if (window.defaultPreprocessor) {
    currentPreprocessor = window.defaultPreprocessor;
    console.log('✓ 图片预处理器已加载');
  } else {
    console.warn('⚠ 图片预处理器未加载，预处理功能将不可用');
  }
  
  bindOcrForms();
  bindMonitorButtons();
  initPreprocessorSettings();
  
  console.log('✓ 客户端初始化完成');
};

document.addEventListener("DOMContentLoaded", init);

