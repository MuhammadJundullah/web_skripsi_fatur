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
  let detectionSummary = null;
  let sessionHealthyCount = 0;
  let sessionUnhealthyCount = 0;

  function getAlertClass(summary) {
    if (!summary) return 'alert-secondary';
    if (summary.needs_immediate_harvest) return 'alert-danger';
    if (summary.overall_status === 'healthy') return 'alert-success';
    return 'alert-secondary';
  }

  function resetSessionCounts() {
    sessionHealthyCount = 0;
    sessionUnhealthyCount = 0;
  }

  // Re-export functions that need to be called from parent
  export function startStreaming() {
    // Logic from App.svelte's startStreaming
    if (isStreaming) return;
    streamingStatus = "Starting camera...";
    detectionSummary = null;
    resetSessionCounts();
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
              return;
            }

            try {
              const message = JSON.parse(event.data);
              if (message.type === 'detection_summary') {
                detectionSummary = message.data;
                sessionHealthyCount = message.data.healthy_count || 0;
                sessionUnhealthyCount = message.data.diseased_count || 0;
              }
            } catch (error) {
              console.error("Failed to parse streaming message:", error);
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
    detectionSummary = null;
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

  {#if detectionSummary}
    <div class={`alert ${getAlertClass(detectionSummary)} mb-3`} role="alert">
      {detectionSummary.recommendation}
    </div>
  {/if}

  <div class="row g-3 mb-3">
    <div class="col-12 col-md-6">
      <div class="card border-0 bg-light h-100">
        <div class="card-body">
          <div class="small text-muted mb-1">{detectionSummary?.healthy_class_name ?? 'Udang Vanamei Sehat'}</div>
          <div class="h4 mb-0 text-success">{sessionHealthyCount}</div>
        </div>
      </div>
    </div>
    <div class="col-12 col-md-6">
      <div class="card border-0 bg-light h-100">
        <div class="card-body">
          <div class="small text-muted mb-1">Total Deteksi Tidak Sehat</div>
          <div class={`h4 mb-0 ${sessionUnhealthyCount > 0 ? 'text-danger' : 'text-success'}`}>{sessionUnhealthyCount}</div>
        </div>
      </div>
    </div>
  </div>

  <div class="row g-3">
    <div class="col-12 col-lg-6">
      <div class="card h-100">
        <div class="card-header">Kamera Langsung</div>
        <div class="card-body">
          <div class="ratio ratio-4x3 bg-dark rounded overflow-hidden position-relative">
            <video class="w-100 h-100 object-fit-contain" bind:this={videoElement} autoplay muted playsinline></video>
            {#if !isStreaming}
              <div class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center text-white bg-dark">
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="bi bi-camera-video-off mb-2" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M10.961 12.365a1.99 1.99 0 0 0 .522-1.103l3.11 1.382A1 1 0 0 0 16 11.731V4.269a1 1 0 0 0-1.406-.913l-3.111 1.382A2 2 0 0 0 9.5 3H4.272l.714 1H9.5a1 1 0 0 1 1 1v6a1 1 0 0 1-.144.525M1.66 10.428 11.166 1H9.5a1 1 0 0 1 1 1v6a1 1 0 0 1-.144.525M1.66 10.428 1.146 9.914a1 1 0 0 1 0-1.414l7.146-7.146a1 1 0 0 1 1.414 0l.514.514zm1.182.883a1.5 1.5 0 0 0 1.5 1.5h4.728l.8 1H4.342a2.5 2.5 0 0 1-2.5-2.5V4.842l1 1v5.47z"/>
                </svg>
                <span class="small">Kamera Nonaktif</span>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <div class="col-12 col-lg-6">
      <div class="card h-100">
        <div class="card-header">Hasil Deteksi</div>
        <div class="card-body">
          <div class="ratio ratio-4x3 bg-dark rounded overflow-hidden position-relative">
            <img class="w-100 h-100 object-fit-contain" bind:this={processedImageElement} alt="Hasil streaming deteksi penyakit udang" />
            {#if !isStreaming || !lastImageUrl}
              <div class="position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center text-white-50 bg-dark">
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" class="bi bi-cpu mb-2" viewBox="0 0 16 16">
                  <path d="M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 .5-.5h.5a.5.5 0 0 1 .5.5v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1.5a.5.5 0 0 1-.5.5h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-.5-.5h-.5a.5.5 0 0 1-.5-.5v-1H2v-1.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2V5H.5a.5.5 0 0 1 0-1H2V3a.5.5 0 0 1 .5-.5h1.5v-1A.5.5 0 0 1 5 0zm-.5 3v10h10V3H4.5zM5 4h9v8H5V4z"/>
                </svg>
                <span class="small">Menunggu Aliran Deteksi</span>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>

  <canvas bind:this={canvasElement} class="d-none"></canvas>
</section>
