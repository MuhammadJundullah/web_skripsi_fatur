<script>
  import { tick } from 'svelte';
  import { apiBaseUrl } from './stores.js';

  export let imageFile;
  export let imagePreviewUrl;
  export let imageResultUrl;
  export let imageStatus;
  export let isCameraActiveForPhoto;
  export let photoCaptureStream;
  export let videoElementForPhoto;
  export let selectedCameraId;

  export let detectionResults = []; 
  let detectionResponse = null;

  function formatPercentage(value) {
    return value.toFixed(2);
  }


  let canvasElement;

  export function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    imageFile = file;
    imagePreviewUrl = URL.createObjectURL(file);
    imageResultUrl = null;
    detectionResults = [];
    detectionResponse = null;
    imageStatus = `Siap menganalisis ${file.name}.`;
  }

  export async function uploadImage() {
    if (!imageFile) return;
    imageStatus = "Mengunggah dan memproses gambar...";
    imageResultUrl = null;
    detectionResults = [];
    detectionResponse = null;

    const formData = new FormData();
    formData.append("file", imageFile);
    try {
      const response = await fetch(`${$apiBaseUrl}/detect/image`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        let errorMsg = `Server error: ${response.status} ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.message || JSON.stringify(errorData);
        } catch {}
        throw new Error(errorMsg);
      }
      
      const responseJson = await response.json();
      imageResultUrl = responseJson.imageUrl;
      detectionResults = responseJson.detections;
      detectionResponse = responseJson;
      imageStatus = "Analisis selesai. Hasil tersedia.";
    } catch (error) {
      console.error("Image upload or detection error:", error);
      imageStatus = `Error: ${error.message}`;
      detectionResults = [];
      detectionResponse = null;
    }
  }

  export async function startCameraForPhoto() {
    imageStatus = "Menyalakan kamera...";
    try {
      isCameraActiveForPhoto = true;
      await tick();
      const constraints = {
        video: {
          width: 640,
          height: 480,
          deviceId: selectedCameraId ? { exact: selectedCameraId } : undefined
        }
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      videoElementForPhoto.srcObject = stream;
      photoCaptureStream = stream;
      await videoElementForPhoto.play();
      imageStatus = "Kamera aktif. Ambil foto untuk analisis.";
    } catch (error) {
      console.error("Failed to start camera for photo:", error);
      imageStatus = "Kamera tidak bisa diakses. Periksa izin browser.";
    }
  }

  export function capturePhoto() {
    if (!videoElementForPhoto || !canvasElement) return;
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElementForPhoto.videoWidth;
    canvasElement.height = videoElementForPhoto.videoHeight;
    context.drawImage(videoElementForPhoto, 0, 0, canvasElement.width, canvasElement.height);
    canvasElement.toBlob((blob) => {
      const capturedFile = new File([blob], "captured_photo.png", { type: "image/png" });
      imageFile = capturedFile;
      imagePreviewUrl = URL.createObjectURL(capturedFile);
      imageResultUrl = null;
      detectionResults = [];
      detectionResponse = null;
      imageStatus = "Foto berhasil diambil. Siap dianalisis.";
      stopCameraForPhoto();
    }, 'image/png');
  }

  export function stopCameraForPhoto() {
    if (photoCaptureStream) {
      photoCaptureStream.getTracks().forEach(track => track.stop());
      photoCaptureStream = null;
    }
    if (videoElementForPhoto) {
      videoElementForPhoto.srcObject = null;
    }
    isCameraActiveForPhoto = false;
    imageStatus = "Kamera dihentikan.";
  }
</script>

<section class="bg-white p-4 rounded-3 shadow-sm mb-4">
  <h2 class="h4 mb-3">Deteksi Penyakit dari Foto Udang</h2>

  <div class="row g-2 align-items-end">
    <div class="col-12 col-md-5">
      <label class="form-label" for="shrimp-image-input">Pilih Gambar Udang</label>
      <input id="shrimp-image-input" type="file" accept="image/*" on:change={handleImageSelect} class="form-control form-control-sm" />
    </div>
    <div class="col-12 col-md-auto">
      <div class="form-label d-block invisible">.</div>
      <button on:click={startCameraForPhoto} disabled={isCameraActiveForPhoto} class="btn btn-secondary btn-sm">Ambil Foto dari Kamera</button>
    </div>
    <div class="col-12 col-md-auto">
      <div class="form-label d-block invisible">.</div>
      <button on:click={uploadImage} disabled={!imageFile} class="btn btn-primary btn-sm">Analisis Foto Udang</button>
    </div>
  </div>

  {#if isCameraActiveForPhoto}
    <div class="card my-3">
      <div class="card-header">Ambil Foto</div>
      <div class="card-body">
        <div class="ratio ratio-4x3 mb-2">
          <video class="w-100 h-100" bind:this={videoElementForPhoto} autoplay muted playsinline></video>
        </div>
        <div class="d-flex gap-2">
          <button on:click={capturePhoto} class="btn btn-primary btn-sm">Ambil Foto</button>
          <button on:click={stopCameraForPhoto} class="btn btn-outline-secondary btn-sm">Hentikan Kamera</button>
        </div>
      </div>
    </div>
  {/if}

  <p class="text-muted small mt-2 mb-3">Status: {imageStatus}</p>

  <div class="row g-3">
    <div class="col-12 col-lg-6">
      <div class="card h-100">
          <div class="card-header">Gambar Asli</div>
        <div class="card-body">
          <img class="img-fluid" src={imagePreviewUrl} alt="Gambar asli udang yang akan dianalisis" />
        </div>
      </div>
    </div>
    <div class="col-12 col-lg-6">
      <div class="card h-100">
          <div class="card-header">Hasil Anotasi</div>
        <div class="card-body">
          <img class="img-fluid" src={imageResultUrl} alt="Hasil deteksi penyakit udang" />
        </div>
      </div>
    </div>
  </div>

  {#if detectionResponse && detectionResponse.summary}
    <div class="mt-4 p-3 bg-light rounded border">
      <h3 class="h5 mb-3">Ringkasan Hasil:</h3>
      <div class="row">
        <div class="col-md-6">
          <p class="mb-1"><strong>Total Udang Terdeteksi:</strong> {detectionResponse.summary.total_count}</p>
          <p class="mb-1"><strong>Udang Sehat:</strong> {detectionResponse.summary.healthy_count} ({formatPercentage(detectionResponse.summary.healthy_percentage)}%)</p>
        </div>
        <div class="col-md-6">
          <p class="mb-1"><strong>Terindikasi Penyakit:</strong> {detectionResponse.summary.diseased_count} ({formatPercentage(detectionResponse.summary.diseased_percentage)}%)</p>
        </div>
      </div>
    </div>
  {/if}

  <canvas bind:this={canvasElement} class="d-none"></canvas>
</section>
