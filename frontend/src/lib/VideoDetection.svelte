<script>
  import { apiBaseUrl } from './stores.js';
  import { onDestroy } from 'svelte';

  let videoFile = null;
  let videoPreviewUrl = null;
  let videoStatus = "Pilih video kolam atau rekam langsung dari kamera.";

  // Recording state
  let isCameraOpen = false;
  let isRecording = false;
  let mediaRecorder;
  let recordedChunks = [];
  let cameraStream;
  let cameraPreviewEl;

  function handleVideoSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    videoFile = file;
    videoPreviewUrl = URL.createObjectURL(file);
    videoStatus = `Siap menganalisis ${file.name}.`;
  }

  async function uploadVideo() {
    if (!videoFile) {
      alert("Pilih atau rekam video terlebih dahulu.");
      return;
    }
    videoStatus = "Mengunggah video...";
    const formData = new FormData();
    formData.append("file", videoFile);
    const apiUrl = `${$apiBaseUrl}/detect/video`;
    
    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
      const data = await response.json();
      videoStatus = `Unggah selesai untuk ${data.original_filename}. Pantau progresnya di riwayat.`;
      videoFile = null;
      videoPreviewUrl = null;
    } catch (error) {
      console.error("Video upload error:", error);
      videoStatus = `Error: ${error.message}`;
    }
  }

  async function openCamera() {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      cameraPreviewEl.srcObject = cameraStream;
      isCameraOpen = true;
    } catch (err) {
      alert("Kamera tidak bisa diakses. Periksa izin browser.");
      console.error("Camera access error:", err);
    }
  }

  function closeCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }
    isCameraOpen = false;
    isRecording = false;
    mediaRecorder = null;
    recordedChunks = [];
  }

  function startRecording() {
    if (!cameraStream) return;
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(cameraStream);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      const fileName = `recording-${new Date().toISOString()}.webm`;
      videoFile = new File([blob], fileName, { type: blob.type });
      videoPreviewUrl = URL.createObjectURL(blob);
      videoStatus = `Rekaman selesai. Siap menganalisis ${fileName}.`;
      closeCamera();
    };
    mediaRecorder.start();
    isRecording = true;
  }

  function stopRecording() {
    if (mediaRecorder) mediaRecorder.stop();
  }

  onDestroy(() => {
    closeCamera();
  });
</script>

<div class="card">
  <div class="card-body">
    <h5 class="card-title">Analisis Video Udang Vannamei</h5>
    <div class="row g-2 align-items-end mb-3">
      <div class="col">
        <label class="form-label" for="shrimp-video-input">Pilih File Video</label>
        <input id="shrimp-video-input" type="file" accept="video/*" on:change={handleVideoSelect} class="form-control" />
      </div>
      <div class="col-auto"> 
        <span class="text-muted">ATAU</span>
      </div>
      <div class="col-auto">
        <div class="form-label">&nbsp;</div>
        <button class="btn btn-secondary" on:click={openCamera}>Rekam dari Kamera</button>
      </div>
    </div>

    {#if videoPreviewUrl}
      <div class="mb-3">
        <h6>Pratinjau & Unggah</h6>
        <video class="w-100 border rounded" src={videoPreviewUrl} controls muted></video>
        <button on:click={uploadVideo} class="btn btn-primary mt-2">Analisis Video</button>
      </div>
    {/if}

    <p class="form-text mb-0">Status: {videoStatus}</p>
  </div>
</div>

{#if isCameraOpen}
  <div class="modal-backdrop fade show"></div>
  <div class="modal fade show" style="display: block;">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Rekam Video Udang</h5>
          <button type="button" class="btn-close" on:click={closeCamera}></button>
        </div>
        <div class="modal-body">
          <video bind:this={cameraPreviewEl} class="w-100" autoplay muted playsinline></video>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" on:click={closeCamera}>Tutup</button>
          {#if isRecording}
            <button type="button" class="btn btn-danger" on:click={stopRecording}>Hentikan Rekaman</button>
          {:else}
            <button type="button" class="btn btn-success" on:click={startRecording}>Mulai Rekam</button>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}
