<script>
  import { onMount, onDestroy } from 'svelte';
  import { Router, Route } from "svelte-routing";
  import { apiBaseUrl, serverStats, initializeApiUrl } from './lib/stores.js';

  // Import page components
  import Dashboard from './pages/Dashboard.svelte';
  import LiveDetection from './pages/LiveDetection.svelte';
  import ImageDetectionPage from './pages/ImageDetectionPage.svelte';
  import BatchProcessing from './pages/BatchProcessing.svelte';
  import Navbar from './lib/Navbar.svelte';

  let monitorSocket;

  // Shared state for camera controls
  let availableCameras = [];
  let selectedCameraId = '';
  let streamingInterval = 200;

  // Component references for cleanup
  let liveDetectionPage;
  let imageDetectionPage;

  function closeMonitorSocket() {
    if (monitorSocket) {
      monitorSocket.close();
      monitorSocket = null;
    }
  }

  function connectMonitorSocket(url) {
    try {
      const parsedUrl = new URL(url);
      const wsProtocol = parsedUrl.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsMonitorUrl = `${wsProtocol}//${parsedUrl.host}/ws/stream/realtime`;

      closeMonitorSocket();
      monitorSocket = new WebSocket(wsMonitorUrl);

      monitorSocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'monitor_stats') {
            serverStats.set(message.data);
          }
        } catch (e) {}
      };
      monitorSocket.onclose = () => {
        serverStats.set(null);
        if (monitorSocket?.readyState === WebSocket.CLOSED) {
          monitorSocket = null;
        }
      };
      monitorSocket.onerror = () => serverStats.set(null);
    } catch (e) {
      console.error("Failed to establish WebSocket connection:", e);
      serverStats.set(null);
    }
  }

  onMount(async () => {
    await initializeApiUrl();

    const unsubscribe = apiBaseUrl.subscribe(url => {
      if (url) {
        connectMonitorSocket(url);
      }
    });

    return () => {
      if (liveDetectionPage && liveDetectionPage.realtimeStreamingComponent) {
        liveDetectionPage.realtimeStreamingComponent.stopStreaming();
      }
      if (imageDetectionPage && imageDetectionPage.imageDetectionComponent) {
        imageDetectionPage.imageDetectionComponent.stopCameraForPhoto();
      }
      closeMonitorSocket();
      unsubscribe();
    };
  });
</script>

<Router>
  <Navbar />

  <main class="container-fluid mt-4">
    <Route path="/">
      <Dashboard serverStats={$serverStats} />
    </Route>
    <Route path="/live">
      <LiveDetection 
        bind:this={liveDetectionPage} 
        bind:availableCameras={availableCameras}
        bind:selectedCameraId={selectedCameraId}
        bind:streamingInterval={streamingInterval}
      />
    </Route>
    <Route path="/image">
      <ImageDetectionPage 
        bind:this={imageDetectionPage}
        bind:selectedCameraId={selectedCameraId}
      />
    </Route>
    <Route path="/batch" component={BatchProcessing} />
  </main>
</Router>
