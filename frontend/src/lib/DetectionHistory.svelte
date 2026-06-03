<script>
  import { onMount } from 'svelte';
  import { apiBaseUrl } from './stores.js';

  let jobs = [];
  let error = null;
  let isLoading = true;

  async function fetchHistory() {
    try {
      const response = await fetch(`${$apiBaseUrl}/history`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      jobs = await response.json();
    } catch (e) {
      error = e.message;
      console.error("Error fetching history:", e);
    } finally {
      isLoading = false;
    }
  }

  async function deleteJob(jobId) {
    if (!confirm('Hapus riwayat proses ini beserta file terkait?')) {
      return;
    }
    try {
      const response = await fetch(`${$apiBaseUrl}/history/${jobId}`, { method: 'DELETE' });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      fetchHistory();
    } catch (e) {
      alert(`Gagal menghapus data: ${e.message}`);
      console.error("Error deleting job:", e);
    }
  }

  async function retryJob(jobId) {
    try {
      const response = await fetch(`${$apiBaseUrl}/retry/${jobId}`, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      fetchHistory();
    } catch (e) {
      alert(`Gagal menjalankan ulang proses: ${e.message}`);
      console.error("Error retrying job:", e);
    }
  }

  function formatDateTime(isoString) {
    if (!isoString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(isoString).toLocaleDateString('en-US', options);
  }

  function formatProgress(job) {
    const value = Number(job.progress_percent ?? 0);
    if (job.status === 'SUCCESS') return 100;
    if (!Number.isFinite(value)) return 0;
    return Math.max(0, Math.min(100, Math.round(value)));
  }

  function formatFrameCount(job) {
    const processed = Number(job.processed_frames ?? 0);
    const total = Number(job.total_frames ?? 0);
    if (total <= 0) return 'Menunggu info frame';
    return `${processed} / ${total} frame`;
  }

  function getHarvestBadgeClass(job) {
    return job.unhealthy_detection_count > 0 ? 'text-bg-danger' : 'text-bg-success';
  }

  function getHarvestLabel(job) {
    return job.unhealthy_detection_count > 0 ? 'Segera Panen' : 'Aman';
  }

  onMount(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 5000);
    return () => clearInterval(interval); 
  });
</script>

<div class="history-container">
  <h2 class="h4 mb-3">Riwayat Analisis Video Udang</h2>
  {#if isLoading}
    <p>Memuat riwayat...</p>
  {:else if error}
    <p class="error">Gagal memuat riwayat: {error}</p>
  {:else if jobs.length === 0}
    <p>Belum ada proses analisis video.</p>
  {:else}
    <button on:click={fetchHistory} class="refresh-btn">Muat Ulang</button>
    <div class="table-responsive">
      <table class="table table-striped table-hover align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nama File</th>
            <th>Status</th>
            <th>Progress</th>
            <th>Deteksi Tidak Sehat</th>
            <th>Rekomendasi</th>
            <th>Waktu Upload</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          {#each jobs as job (job.id)}
            <tr>
              <td>{job.id}</td>
              <td>{job.original_filename || job.filename}</td>
              <td>
                <span class={`badge status-badge status-${job.status.toLowerCase()}`}>{job.status}</span>
                {#if job.status === 'FAILURE' && job.error_message}
                  <div class="failure-message">{job.error_message}</div>
                {/if}
              </td>
              <td class="progress-cell">
                <div class="progress-wrapper">
                  <div class="progress">
                    <div
                      class="progress-bar"
                      class:progress-bar-striped={job.status === 'PROCESSING'}
                      class:progress-bar-animated={job.status === 'PROCESSING'}
                      role="progressbar"
                      style={`width: ${formatProgress(job)}%;`}
                      aria-valuenow={formatProgress(job)}
                      aria-valuemin="0"
                      aria-valuemax="100"
                    >
                      {formatProgress(job)}%
                    </div>
                  </div>
                  <small class="text-muted">{formatProgress(job)}% - {formatFrameCount(job)}</small>
                </div>
              </td>
              <td>{job.unhealthy_detection_count}</td>
              <td>
                <span class={`badge ${getHarvestBadgeClass(job)}`}>{getHarvestLabel(job)}</span>
              </td>
              <td>{formatDateTime(job.upload_time)}</td>
              <td class="actions">
                {#if job.status === 'SUCCESS'}
                  <a href="{$apiBaseUrl}/download/{job.id}" class="btn btn-sm btn-outline-success">Unduh</a>
                {/if}
                {#if job.status === 'FAILURE'}
                  <button on:click={() => retryJob(job.id)} class="btn btn-sm btn-outline-warning">Coba Lagi</button>
                {/if}
                <button on:click={() => deleteJob(job.id)} class="btn btn-sm btn-outline-danger">Hapus</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .history-container { margin-top: 2rem; padding: 1.5rem; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  h2 { margin-top: 0; color: #333; }
  th, td { white-space: nowrap; vertical-align: middle; }
  .refresh-btn { padding: 0.5rem 1rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 1rem; }
  .refresh-btn:hover { background-color: #0056b3; }
  .status-badge { color: white !important; }
  .status-pending { background-color: #ffc107; }
  .status-processing { background-color: #17a2b8; }
  .status-success { background-color: #28a745; }
  .status-failure { background-color: #dc3545; }
  .progress-cell { min-width: 220px; }
  .progress-wrapper { display: grid; gap: 0.25rem; }
  .progress { height: 1.25rem; background-color: #e9ecef; }
  .progress-bar { background-color: #0d6efd; color: white; font-size: 0.75rem; line-height: 1.25rem; }
  .failure-message { max-width: 320px; margin-top: 0.25rem; color: #dc3545; font-size: 0.8rem; white-space: normal; }
  .actions { display: flex; gap: 0.5rem; }
  .error { color: #dc3545; }
</style>
