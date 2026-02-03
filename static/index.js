const state = {
  url: "",
  mediaType: "video",
  quality: "1080",
  videoCodec: "mp4",
  bitrate: "256",
  audioCodec: "mp3",
  availableQualities: [],
  isDownloading: false,
  isYouTubeMusic: false,
};

const elements = {
  urlInput: document.getElementById("urlInput"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  entryState: document.getElementById("entryState"),
  loadingState: document.getElementById("loadingState"),
  mediaInfo: document.getElementById("mediaInfo"),
  errorMessage: document.getElementById("errorMessage"),
  successMessage: document.getElementById("successMessage"),
  howItWorks: document.getElementById("howItWorks"),
  thumbnail: document.getElementById("thumbnail"),
  videoTitle: document.getElementById("videoTitle"),
  videoAuthor: document.getElementById("videoAuthor"),
  downloadBtn: document.getElementById("downloadBtn"),
  backBtn: document.getElementById("backBtn"),
  videoControls: document.getElementById("videoControls"),
  audioControls: document.getElementById("audioControls"),
  qualityButtons: document.getElementById("qualityButtons"),
  downloadProgress: document.getElementById("downloadProgress"),
  logo: document.querySelector(".logo"),
  card: document.querySelector(".card"),
  mediaTypeGroup: document.getElementById("mediaTypeGroup"),
  bitrateGroup: document.getElementById("bitrateGroup"),
};

elements.analyzeBtn.addEventListener("click", analyzeVideo);
elements.downloadBtn.addEventListener("click", downloadMedia);
elements.backBtn.addEventListener("click", reset);

elements.urlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") analyzeVideo();
});

document.querySelectorAll("[data-type]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document
      .querySelectorAll("[data-type]")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    state.mediaType = e.target.dataset.type;
    toggleMediaControls();
  });
});

document.querySelectorAll("[data-quality]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    if (!e.target.disabled) {
      document
        .querySelectorAll("[data-quality]")
        .forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");
      state.quality = e.target.dataset.quality;
    }
  });
});

document.querySelectorAll("[data-codec]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document
      .querySelectorAll("[data-codec]")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    state.videoCodec = e.target.dataset.codec;
  });
});

document.querySelectorAll("[data-bitrate]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document
      .querySelectorAll("[data-bitrate]")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    state.bitrate = e.target.dataset.bitrate;
  });
});

document.querySelectorAll("[data-audio-format]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document
      .querySelectorAll("[data-audio-format]")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    state.audioCodec = e.target.dataset.audioFormat;

    if (e.target.dataset.audioFormat === "wav") {
      elements.bitrateGroup.classList.add("hidden");
    } else {
      elements.bitrateGroup.classList.remove("hidden");
    }
  });
});

function toggleMediaControls() {
  if (state.mediaType === "video") {
    elements.videoControls.classList.remove("hidden");
    elements.audioControls.classList.add("hidden");
  } else {
    elements.videoControls.classList.add("hidden");
    elements.audioControls.classList.remove("hidden");

    if (state.audioCodec === "wav") {
      elements.bitrateGroup.classList.add("hidden");
    } else {
      elements.bitrateGroup.classList.remove("hidden");
    }
  }
}

async function analyzeVideo() {
  let url = elements.urlInput.value.trim();

  if (!url) {
    showError("Please enter a YouTube URL");
    return;
  }

  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }

  state.url = url;
  state.isYouTubeMusic = url.includes("music.youtube.com");

  hideError();
  elements.entryState.classList.add("hidden");
  elements.loadingState.style.display = "block";
  elements.howItWorks.classList.add("hidden");

  try {
    const response = await fetch("/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      let errorMessage = "Failed to analyze video";

      if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail[0].msg;
      } else if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    displayMediaInfo(data);
  } catch (error) {
    showError(error.message);
    elements.loadingState.style.display = "none";
    elements.entryState.classList.remove("hidden");
    elements.howItWorks.classList.remove("hidden");
  }
}

function displayMediaInfo(data) {
  elements.logo.classList.add("hidden-logo");
  elements.backBtn.classList.remove("hidden");

  elements.thumbnail.src = data.thumbnail;
  elements.videoTitle.textContent = data.title;
  elements.videoAuthor.textContent = data.author || "Unknown";

  state.availableQualities = data.available_qualities || [];

  const isAudioOnly =
    state.availableQualities.length === 0 ||
    (data.is_live === false && state.availableQualities.every((q) => q < 144));

  if (state.isYouTubeMusic || isAudioOnly) {
    state.mediaType = "audio";
    elements.mediaTypeGroup.classList.add("hidden");
    toggleMediaControls();
  } else {
    elements.mediaTypeGroup.classList.remove("hidden");

    document.querySelectorAll("[data-quality]").forEach((btn) => {
      const quality = parseInt(btn.dataset.quality);
      if (state.availableQualities.includes(quality)) {
        btn.disabled = false;
        btn.style.opacity = "1";
      } else {
        btn.disabled = true;
        btn.style.opacity = "0.3";
      }
    });

    const firstAvailable = state.availableQualities[0];
    if (firstAvailable) {
      state.quality = firstAvailable.toString();
      document.querySelectorAll("[data-quality]").forEach((btn) => {
        btn.classList.remove("active");
        if (btn.dataset.quality === state.quality) {
          btn.classList.add("active");
        }
      });
    }
  }

  elements.loadingState.style.display = "none";
  elements.mediaInfo.style.display = "block";
}

async function downloadMedia() {
  if (state.isDownloading) return;

  state.isDownloading = true;
  elements.downloadBtn.disabled = true;
  elements.downloadProgress.classList.remove("hidden");
  hideError();

  try {
    const response = await fetch("/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: state.url,
        media_type: state.mediaType,
        quality: state.quality,
        video_codec: state.videoCodec,
        bitrate: state.bitrate,
        audio_codec: state.audioCodec,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      let errorMessage = "An error occurred";

      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail[0].msg;
      }
      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const xFileName = response.headers.get("X-File-Name");
    let filename = "download";

    if (xFileName) {
      try {
        const binString = atob(xFileName);
        const bytes = Uint8Array.from(binString, (m) => m.codePointAt(0));
        filename = new TextDecoder().decode(bytes);
        console.log("Filename from X-File-Name:", filename);
      } catch (e) {
        console.error("Error decoding X-File-Name:", e);
      }
    } else {
        const contentDisposition = response.headers.get("content-disposition");
        if (contentDisposition) {
            const match = contentDisposition.match(/filename\*=UTF-8''([^;%\n]*)/);
            if (match) filename = decodeURIComponent(match[1]);
        }
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    showSuccess();
  } catch (error) {
    showError(error.message);
  } finally {
    state.isDownloading = false;
    elements.downloadBtn.disabled = false;
    elements.downloadProgress.classList.add("hidden");
  }
}

function showError(message) {
  elements.errorMessage.textContent = message;
  elements.errorMessage.style.display = "block";
}

function hideError() {
  elements.errorMessage.style.display = "none";
}

function showSuccess() {
  elements.card.classList.add("success-flash");
  setTimeout(() => {
    elements.card.classList.remove("success-flash");
  }, 1000);
}

function reset() {
  elements.logo.classList.remove("hidden-logo");
  elements.backBtn.classList.add("hidden");
  elements.mediaInfo.style.display = "none";
  elements.entryState.classList.remove("hidden");
  elements.howItWorks.classList.remove("hidden");
  elements.urlInput.value = "";
  elements.successMessage.style.display = "none";
  elements.mediaTypeGroup.classList.remove("hidden");
  elements.bitrateGroup.classList.remove("hidden");
  hideError();

  state.mediaType = "video";
  state.quality = "1080";
  state.videoCodec = "mp4";
  state.bitrate = "256";
  state.audioCodec = "mp3";
  state.isYouTubeMusic = false;

  document
    .querySelectorAll("[data-type]")
    .forEach((b) => b.classList.remove("active"));
  document.querySelector('[data-type="video"]').classList.add("active");

  document
    .querySelectorAll("[data-audio-format]")
    .forEach((b) => b.classList.remove("active"));
  document.querySelector('[data-audio-format="mp3"]').classList.add("active");

  toggleMediaControls();
}
