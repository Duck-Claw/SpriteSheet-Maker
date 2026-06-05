const state = {
  inputPath: "",
  filename: "",
  language: "zh",
};

const translations = {
  zh: {
    languageToggle: "EN",
    inputTitle: "输入",
    fileTextDefault: "选择视频、GIF 或图片",
    frameRangeTitle: "帧范围",
    fpsPresetLabel: "帧率预设",
    fpsOriginalOption: "原始",
    fpsCustomOption: "自定义",
    customFpsLabel: "自定义 FPS",
    startFrameLabel: "起始帧",
    endFrameLabel: "结束帧",
    transparencyTitle: "透明处理",
    removeBlackLabel: "移除黑底",
    blackThresholdLabel: "黑色阈值",
    softEdgeLabel: "柔边",
    alphaStrengthLabel: "Alpha 强度",
    frameCanvasTitle: "单帧画布",
    autoSizeLabel: "自动尺寸",
    anchorLabel: "锚点",
    anchorCenterOption: "居中",
    anchorTopOption: "顶部",
    anchorBottomOption: "底部",
    widthLabel: "宽度",
    heightLabel: "高度",
    spriteSheetTitle: "宫格图",
    layoutModeLabel: "布局模式",
    fpsAutoOption: "帧率自动布局",
    customGridOption: "自定义行列",
    columnsLabel: "列数",
    rowsLabel: "行数",
    paddingLabel: "单帧四周留白",
    maxTextureLabel: "最大贴图",
    gridPriorityLabel: "填满自定义行列",
    tightGridLabel: "无留白",
    outputPngLabel: "输出 PNG",
    saveFolderLabel: "保存目录",
    chooseOutputDirBtn: "选择",
    exportFramesLabel: "导出单帧文件夹",
    previewBtn: "预览",
    exportBtn: "导出",
    previewTitle: "预览",
    bgCheckerOption: "棋盘格",
    bgBlackOption: "黑底",
    bgWhiteOption: "白底",
    bgGrayOption: "灰底",
    bgTransparentOption: "透明",
    emptyState: "上传素材后点击预览或导出。",
    ready: "就绪。",
    uploading: "正在上传素材...",
    uploaded: "素材已上传，可以预览。",
    chooseInput: "请先选择输入素材。",
    buildingPreview: "正在生成预览...",
    refreshingPreview: "正在刷新预览...",
    exporting: "正在导出宫格图...",
    choosingFolder: "正在打开保存目录选择器...",
    saveFolder: "保存目录",
    exported: "已导出",
    previewStatus: "预览",
    sheetSizeLabel: "图片",
    frameCanvasSizeLabel: "单帧",
    actualFpsLabel: "实际 FPS",
    previewImageMissing: "没有返回预览图。",
    previewImageFailed: "预览图加载失败。",
    customFpsPlaceholder: "仅自定义",
    allPlaceholder: "全部",
    autoPlaceholder: "自动",
  },
  en: {
    languageToggle: "中",
    inputTitle: "Input",
    fileTextDefault: "Choose video, GIF, or image",
    frameRangeTitle: "Frame Range",
    fpsPresetLabel: "FPS Preset",
    fpsOriginalOption: "Original",
    fpsCustomOption: "Custom",
    customFpsLabel: "Custom FPS",
    startFrameLabel: "Start Frame",
    endFrameLabel: "End Frame",
    transparencyTitle: "Transparency",
    removeBlackLabel: "Remove Black Background",
    blackThresholdLabel: "Black Threshold",
    softEdgeLabel: "Soft Edge",
    alphaStrengthLabel: "Alpha Strength",
    frameCanvasTitle: "Frame Canvas",
    autoSizeLabel: "Auto Size",
    anchorLabel: "Anchor",
    anchorCenterOption: "Center",
    anchorTopOption: "Top",
    anchorBottomOption: "Bottom",
    widthLabel: "Width",
    heightLabel: "Height",
    spriteSheetTitle: "Sprite Sheet",
    layoutModeLabel: "Layout Mode",
    fpsAutoOption: "FPS Auto Grid",
    customGridOption: "Custom Rows / Columns",
    columnsLabel: "Columns",
    rowsLabel: "Rows",
    paddingLabel: "Frame Margin",
    maxTextureLabel: "Max Texture",
    gridPriorityLabel: "Fill custom grid",
    tightGridLabel: "No margin",
    outputPngLabel: "Output PNG",
    saveFolderLabel: "Save Folder",
    chooseOutputDirBtn: "Choose",
    exportFramesLabel: "Export frames folder",
    previewBtn: "Preview",
    exportBtn: "Export",
    previewTitle: "Preview",
    bgCheckerOption: "Checker",
    bgBlackOption: "Black",
    bgWhiteOption: "White",
    bgGrayOption: "Gray",
    bgTransparentOption: "Transparent",
    emptyState: "Upload a source file, then preview or export.",
    ready: "Ready.",
    uploading: "Uploading source...",
    uploaded: "Source uploaded. Preview when ready.",
    chooseInput: "Choose an input file first.",
    buildingPreview: "Building preview...",
    refreshingPreview: "Refreshing preview...",
    exporting: "Exporting sprite sheet...",
    choosingFolder: "Opening output folder picker...",
    saveFolder: "Save folder",
    exported: "Exported",
    previewStatus: "Preview",
    sheetSizeLabel: "Image",
    frameCanvasSizeLabel: "Frame",
    actualFpsLabel: "Actual FPS",
    previewImageMissing: "Preview image was not returned.",
    previewImageFailed: "Preview image failed to load.",
    customFpsPlaceholder: "Only Custom",
    allPlaceholder: "All",
    autoPlaceholder: "Auto",
  },
};

const els = Object.fromEntries(
  [
    "fileInput",
    "fileText",
    "languageToggle",
    "inputTitle",
    "fpsPreset",
    "fpsPresetLabel",
    "fpsOriginalOption",
    "fpsCustomOption",
    "fps",
    "customFpsLabel",
    "startFrame",
    "startFrameLabel",
    "endFrame",
    "endFrameLabel",
    "frameRangeTitle",
    "transparencySection",
    "transparencyToggle",
    "transparencyTitle",
    "removeBlack",
    "removeBlackLabel",
    "blackThreshold",
    "blackThresholdLabel",
    "blackThresholdOut",
    "softEdge",
    "softEdgeLabel",
    "softEdgeOut",
    "alphaStrength",
    "alphaStrengthLabel",
    "autoSize",
    "autoSizeLabel",
    "frameCanvasTitle",
    "frameWidth",
    "widthLabel",
    "frameHeight",
    "heightLabel",
    "anchor",
    "anchorLabel",
    "anchorCenterOption",
    "anchorTopOption",
    "anchorBottomOption",
    "columns",
    "columnsLabel",
    "rows",
    "rowsLabel",
    "padding",
    "paddingLabel",
    "maxTextureSize",
    "maxTextureLabel",
    "layoutMode",
    "layoutModeLabel",
    "fpsAutoOption",
    "customGridOption",
    "gridPriority",
    "gridPriorityLabel",
    "tightGrid",
    "tightGridLabel",
    "outputName",
    "outputPngLabel",
    "outputDir",
    "saveFolderLabel",
    "chooseOutputDirBtn",
    "exportFrames",
    "exportFramesLabel",
    "spriteSheetTitle",
    "background",
    "bgCheckerOption",
    "bgBlackOption",
    "bgWhiteOption",
    "bgGrayOption",
    "bgTransparentOption",
    "previewBtn",
    "exportBtn",
    "previewTitle",
    "previewImage",
    "emptyState",
    "status",
    "progressBar",
    "progressText",
  ].map((id) => [id, document.getElementById(id)])
);

els.outputDir.value = "assets/output";
applyLanguage();
syncFpsInput();
syncGridControls();

for (const [slider, output] of [
  [els.blackThreshold, els.blackThresholdOut],
  [els.softEdge, els.softEdgeOut],
]) {
  slider.addEventListener("input", () => {
    output.textContent = slider.value;
  });
}

els.fileInput.addEventListener("change", async () => {
  const file = els.fileInput.files[0];
  if (!file) return;
  setStatus(t("uploading"));
  const form = new FormData();
  form.append("file", file);
  const result = await postForm("/api/upload", form);
  state.inputPath = result.path;
  state.filename = result.filename;
  els.fileText.textContent = result.filename;
  els.outputName.value = `${result.filename.replace(/\.[^.]+$/, "")}_sheet.png`;
  setStatus(t("uploaded"));
});

els.languageToggle.addEventListener("click", () => {
  state.language = state.language === "zh" ? "en" : "zh";
  applyLanguage();
});

els.transparencyToggle.addEventListener("click", () => {
  const collapsed = els.transparencySection.classList.toggle("collapsed");
  els.transparencyToggle.textContent = collapsed ? "▸" : "▾";
});

els.fpsPreset.addEventListener("change", syncFpsInput);
els.layoutMode.addEventListener("change", syncGridControls);
els.tightGrid.addEventListener("change", () => {
  if (els.tightGrid.checked) {
    els.padding.value = "0";
  }
});

els.previewBtn.addEventListener("click", async () => {
  await runJob("/api/preview", t("buildingPreview"));
});

els.chooseOutputDirBtn.addEventListener("click", async () => {
  setStatus(t("choosingFolder"));
  try {
    const result = await postJson("/api/choose-output-dir", {});
    els.outputDir.value = result.outputDir;
    setStatus(`${t("saveFolder")}: ${result.outputDir}`);
  } catch (error) {
    setStatus(error.message);
  }
});

els.exportBtn.addEventListener("click", async () => {
  await runJob("/api/export", t("exporting"));
});

els.background.addEventListener("change", async () => {
  if (state.inputPath) {
    await runJob("/api/preview", t("refreshingPreview"));
  }
});

async function runJob(url, label) {
  if (!state.inputPath) {
    setStatus(t("chooseInput"));
    return;
  }
  setBusy(true);
  setStatus(label);
  setProgress(0);
  try {
    const started = await postJson(url, readPayload());
    const result = await pollJob(started.jobId);
    showImage(result.image);
    if (result.outputPath) {
      setStatus(`${t("exported")}: ${result.outputPath}`);
    } else {
      setStatus(formatPreviewStatus(result));
    }
  } catch (error) {
    setStatus(error.message);
    setProgress(100);
  } finally {
    setBusy(false);
  }
}

function readPayload() {
  const fpsPreset = els.fpsPreset.value;
  const fpsValue = fpsPreset === "custom" ? valueOrNull(els.fps.value) : valueOrNull(fpsPreset);
  return {
    inputPath: state.inputPath,
    fps: fpsValue,
    startFrame: valueOrNull(els.startFrame.value),
    endFrame: valueOrNull(els.endFrame.value),
    removeBlack: els.removeBlack.checked,
    blackThreshold: Number(els.blackThreshold.value),
    softEdge: Number(els.softEdge.value),
    alphaStrength: Number(els.alphaStrength.value || 1),
    autoSize: els.autoSize.checked,
    frameWidth: valueOrNull(els.frameWidth.value),
    frameHeight: valueOrNull(els.frameHeight.value),
    anchor: els.anchor.value,
    layoutMode: els.layoutMode.value,
    columns: valueOrNull(els.columns.value),
    rows: valueOrNull(els.rows.value),
    padding: Number(els.padding.value || 0),
    maxTextureSize: valueOrNull(els.maxTextureSize.value),
    gridPriority: els.gridPriority.checked,
    tightGrid: els.tightGrid.checked,
    outputName: els.outputName.value || "sprite_sheet.png",
    outputDir: els.outputDir.value || "assets/output",
    exportFrames: els.exportFrames.checked,
    background: els.background.value,
  };
}

async function pollJob(jobId) {
  while (true) {
    const response = await fetch(`/api/job?id=${encodeURIComponent(jobId)}`);
    const job = await parseResponse(response);
    setProgress(job.progress || 0);
    if (job.message) {
      setStatus(job.message);
    }
    if (job.state === "done") {
      setProgress(100);
      return job;
    }
    if (job.state === "error") {
      throw new Error(job.error || job.message || "Job failed.");
    }
    await delay(250);
  }
}

function valueOrNull(value) {
  return value === "" ? null : value;
}

function formatFps(value) {
  const fps = Number(value);
  if (!Number.isFinite(fps) || fps <= 0) return "";
  return `${fps.toFixed(fps >= 10 ? 1 : 2).replace(/\.?0+$/, "")} FPS`;
}

function formatPreviewStatus(result) {
  const parts = [
    `${result.frameCount} frames`,
    `${t("sheetSizeLabel")} ${formatSize(result.sheetWidth, result.sheetHeight)}`,
    `${t("frameCanvasSizeLabel")} ${formatSize(result.frameWidth, result.frameHeight)}`,
    `${result.columns}x${result.rows}`,
  ];
  const fpsText = formatFps(result.effectiveFps);
  if (fpsText) {
    parts.push(`${t("actualFpsLabel")} ${fpsText}`);
  }
  return `${t("previewStatus")}: ${parts.join(", ")}`;
}

function formatSize(width, height) {
  const numericWidth = Number(width);
  const numericHeight = Number(height);
  if (!Number.isFinite(numericWidth) || !Number.isFinite(numericHeight)) {
    return "-";
  }
  return `${numericWidth}x${numericHeight}`;
}

function showImage(src) {
  if (!src) {
    throw new Error(t("previewImageMissing"));
  }
  els.previewImage.onload = () => {
    els.previewImage.style.display = "block";
    els.emptyState.style.display = "none";
  };
  els.previewImage.onerror = () => {
    setStatus(t("previewImageFailed"));
  };
  els.previewImage.src = src;
}

function setStatus(text) {
  els.status.textContent = text;
}

function setProgress(value) {
  const next = Math.max(0, Math.min(100, Number(value) || 0));
  els.progressBar.value = next;
  els.progressText.textContent = `${Math.round(next)}%`;
}

function setBusy(isBusy) {
  els.previewBtn.disabled = isBusy;
  els.exportBtn.disabled = isBusy;
  els.chooseOutputDirBtn.disabled = isBusy;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function syncFpsInput() {
  const isCustom = els.fpsPreset.value === "custom";
  els.fps.disabled = !isCustom;
  if (!isCustom) {
    els.fps.value = "";
  }
}

function syncGridControls() {
  const isCustomGrid = els.layoutMode.value === "customGrid";
  els.rows.disabled = !isCustomGrid;
  els.gridPriority.disabled = !isCustomGrid;
  els.tightGrid.disabled = !isCustomGrid;
  if (!isCustomGrid) {
    els.rows.value = "";
    els.gridPriority.checked = false;
    els.tightGrid.checked = false;
  }
}

function applyLanguage() {
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  for (const [key, value] of Object.entries(translations[state.language])) {
    if (!els[key]) continue;
    if (key.endsWith("Placeholder")) continue;
    els[key].textContent = value;
  }
  els.fps.placeholder = t("customFpsPlaceholder");
  els.endFrame.placeholder = t("allPlaceholder");
  els.columns.placeholder = t("autoPlaceholder");
  els.rows.placeholder = t("autoPlaceholder");
  if (!state.filename) {
    els.fileText.textContent = t("fileTextDefault");
  }
  if (els.status.textContent === translations.zh.ready || els.status.textContent === translations.en.ready) {
    setStatus(t("ready"));
  }
}

function t(key) {
  return translations[state.language][key] || key;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

async function postForm(url, form) {
  const response = await fetch(url, { method: "POST", body: form });
  return parseResponse(response);
}

async function parseResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}
