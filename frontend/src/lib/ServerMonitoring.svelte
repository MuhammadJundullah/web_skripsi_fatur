<script>
  export let serverStats = null;
</script>

<section class="bg-white p-4 rounded-3 shadow-sm mb-4">
  <h2 class="h4 mb-3">Monitoring Server</h2>

  {#if serverStats}
    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-3">
      <div class="col">
        <div class="card border-0 bg-light">
          <div class="card-body">
            <span class="stat-label d-block small text-secondary mb-1">Penggunaan CPU</span>
            <span class="stat-value fs-4 fw-semibold text-dark">{serverStats.cpu_percent.toFixed(1)}%</span>
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card border-0 bg-light">
          <div class="card-body">
            <span class="stat-label d-block small text-secondary mb-1">Penggunaan Memori</span>
            <span class="stat-value fs-4 fw-semibold text-dark">{serverStats.memory.percent.toFixed(1)}%</span>
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card border-0 bg-light">
          <div class="card-body">
            <span class="stat-label d-block small text-secondary mb-1">Memori Terpakai</span>
            <span class="stat-value fs-4 fw-semibold text-dark">{(serverStats.memory.used / (1024**3)).toFixed(2)} GB / {(serverStats.memory.total / (1024**3)).toFixed(2)} GB</span>
          </div>
        </div>
      </div>
      {#if serverStats.gpu}
        <div class="col">
          <div class="card border-0 bg-light">
            <div class="card-body">
              <span class="stat-label d-block small text-secondary mb-1">Perangkat Deteksi (GPU)</span>
              {#if serverStats.gpu.available}
                <span class="stat-value fs-6 fw-semibold text-success d-block text-truncate" title={serverStats.gpu.name}>{serverStats.gpu.name}</span>
                <span class="stat-sublabel small text-muted d-block" style="font-size: 0.75rem;">VRAM: {serverStats.gpu.allocated_mb} MB / {serverStats.gpu.reserved_mb} MB</span>
              {:else}
                <span class="stat-value fs-4 fw-semibold text-secondary">CPU Mode</span>
                <span class="stat-sublabel small text-muted">Tidak ada GPU terdeteksi</span>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="alert alert-secondary mb-0">Mengambil statistik server...</div>
  {/if}
</section>
