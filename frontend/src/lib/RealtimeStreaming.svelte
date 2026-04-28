<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { apiBaseUrl } from './stores.js';

  const dispatch = createEventDispatcher();

  export let videoElement;
  export let processedImageElement;
  export let streamingSocket;
  export let isStreaming;
  export let intervalId;
  export let streamingStatus;
  export let lastImageUrl;
  export let availableCameras;
  export let selectedCameraId;
  export let streamingInterval;
  export let intervalOptions;

  let canvasElement; // Managed internally by RealtimeStreaming

  // Re-export functions that need to be called from parent
  export function startStreaming() {
    // Logic from App.svelte's startStreaming
    if (isStreaming) return;
    streamingStatus = "Starting camera...";
    try {
      const constraints = {
        video: {
          width: 320,
          height: 240,
          deviceId: selectedCameraId ? { exact: selectedCameraId } : undefined
        }
      };
      navigator.mediaDevices.getUserMedia(constraints).then(stream => {
        videoElement.srcObject = stream;
        videoElement.play().then(() => {
          streamingStatus = "Connecting to server...";
          const url = new URL($apiBaseUrl);
          const wsProtocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
          const wsUrl = `${wsProtocol}//${url.host}/ws/stream/realtime`;
          streamingSocket = new WebSocket(wsUrl);
          streamingSocket.onopen = () => {
            streamingStatus = "Connection open. Streaming...";
            isStreaming = true;
            intervalId = setInterval(() => {
              if (streamingSocket.readyState === WebSocket.OPEN) sendFrame();
            }, streamingInterval);
          };
          streamingSocket.onmessage = async (event) => {
            if (event.data instanceof Blob) { // Handle video frames
              if (lastImageUrl) URL.revokeObjectURL(lastImageUrl);
              const imageUrl = URL.createObjectURL(event.data);
              processedImageElement.src = imageUrl;
              lastImageUrl = imageUrl;
            }
          };
          streamingSocket.onclose = () => {
            streamingStatus = "Connection closed.";
            stopStreaming(false);
          };
          streamingSocket.onerror = (error) => {
            console.error("WebSocket Error (Streaming):", error);
            streamingStatus = "Connection error. See console.";
            stopStreaming();
          };
        }).catch(error => {
          console.error("Failed to play video:", error);
          streamingStatus = "Could not play video.";
        });
      }).catch(error => {
        console.error("Failed to start camera:", error);
        streamingStatus = "Could not start camera. Check permissions.";
      });
    } catch (error) {
      console.error("Failed to start camera:", error);
      streamingStatus = "Could not start camera. Check permissions.";
    }
  }

  export function stopStreaming(closeSocket = true) {
    // Logic from App.svelte's stopStreaming
    if (!isStreaming && !videoElement?.srcObject) return;
    isStreaming = false;
    clearInterval(intervalId);
    if (closeSocket && streamingSocket) streamingSocket.close();
    if (videoElement?.srcObject) {
      videoElement.srcObject.getTracks().forEach(track => track.stop());
      videoElement.srcObject = null;
    }
    if (lastImageUrl) {
      URL.revokeObjectURL(lastImageUrl);
      lastImageUrl = null;
    }
    if (processedImageElement) processedImageElement.src = '';
    if (streamingStatus.startsWith("Connection open")) {
      streamingStatus = "Streaming stopped.";
    }
  }

  function sendFrame() {
    if (!videoElement || !canvasElement) return;
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    canvasElement.toBlob((blob) => {
      if (streamingSocket && streamingSocket.readyState === WebSocket.OPEN) streamingSocket.send(blob);
    }, 'image/jpeg', 0.8);
  }

  function toggleFullscreen() {
    if (processedImageElement && document.fullscreenElement !== processedImageElement) {
      processedImageElement.requestFullscreen().catch(err => {
        alert(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  onMount(() => {
    // Initial camera load logic from App.svelte's onMount
    navigator.mediaDevices.enumerateDevices().then(devices => {
      availableCameras = devices.filter(device => device.kind === 'videoinput');
      if (availableCameras.length > 0 && !selectedCameraId) {
        selectedCameraId = availableCameras[0].deviceId;
      }
    }).catch(error => {
      console.error("Error enumerating media devices.", error);
    });
  });

  onDestroy(() => {
    stopStreaming();
  });
</script>

<section class="bg-white p-4 rounded-3 shadow-sm mb-4">
  <h2 class="h4 mb-3">Deteksi Real-time Udang Vannamei</h2>

  <div class="row g-2 align-items-end">
    <div class="col-auto">
      <button on:click={startStreaming} disabled={isStreaming} class="btn btn-primary btn-sm">Mulai Streaming</button>
    </div>
    <div class="col-auto">
      <button on:click={() => stopStreaming()} disabled={!isStreaming} class="btn btn-outline-primary btn-sm">Hentikan Streaming</button>
    </div>
    <div class="col-auto">
      <button on:click={toggleFullscreen} disabled={!isStreaming} class="btn btn-outline-secondary btn-sm">Layar Penuh</button>
    </div>

    <div class="col-12 col-md-3">
      <label for="interval-select" class="form-label mb-1">Kecepatan Frame</label>
      <select id="interval-select" class="form-select form-select-sm" bind:value={streamingInterval} disabled={isStreaming}>
        {#each intervalOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    </div>

    <div class="col-12 col-md-4">
      <label for="camera-select" class="form-label mb-1">Kamera</label>
      <select id="camera-select" class="form-select form-select-sm"
              bind:value={selectedCameraId} disabled={isStreaming || availableCameras.length === 0}>
        {#if availableCameras.length === 0}
          <option value="">Kamera tidak ditemukan</option>
        {/if}
        {#each availableCameras as camera}
          <option value={camera.deviceId}>{camera.label || `Camera ${camera.deviceId.substring(0, 6)}`}</option>
        {/each}
      </select>
    </div>
  </div>

  <p class="text-muted small mt-2 mb-3">Status: {streamingStatus}</p>

  <div class="row g-3">
    <div class="col-12 col-lg-6">
      <div class="card h-100">
          <div class="card-header">Kamera Langsung</div>
        <div class="card-body">
          <div class="ratio ratio-4x3">
            <video class="w-100 h-100" bind:this={videoElement} autoplay muted playsinline></video>
          </div>
        </div>
      </div>
    </div>

    <div class="col-12 col-lg-6">
      <div class="card h-100">
          <div class="card-header">Hasil Deteksi</div>
        <div class="card-body">
          <img class="img-fluid border" bind:this={processedImageElement} alt="Hasil streaming deteksi penyakit udang" />
        </div>
      </div>
    </div>
  </div>

  <canvas bind:this={canvasElement} class="d-none"></canvas>
</section>
