<script>
  import ApiConfiguration from '../lib/ApiConfiguration.svelte';
  import ServerMonitoring from '../lib/ServerMonitoring.svelte';
  import ModelConfiguration from '../lib/ModelConfiguration.svelte';

  export let serverStats;
</script>

<div class="row">
  <div class="col-12 mb-4">
    <section class="dashboard-hero p-4 p-lg-5 rounded-4 shadow-sm">
      <span class="hero-kicker">Monitoring Budidaya Udang</span>
      <h1 class="h3 mt-2 mb-3">Panel deteksi penyakit udang vannamei untuk foto, video, dan pemantauan real-time.</h1>
      <p class="mb-0 text-secondary">
        Gunakan dashboard ini untuk mengatur endpoint API, ambang confidence model, dan memantau performa server selama proses deteksi.
      </p>
    </section>
  </div>
  <div class="col-lg-5 mb-4">
    <ApiConfiguration />
  </div>
  <div class="col-lg-5 mb-4">
    <ModelConfiguration />
  </div>
  <ServerMonitoring {serverStats} />
</div>

<style>
  .dashboard-hero {
    background:
      radial-gradient(circle at top right, rgba(0, 153, 153, 0.20), transparent 28%),
      linear-gradient(135deg, #f5fcfb 0%, #e6f5f4 45%, #eef9f8 100%);
    border: 1px solid rgba(0, 96, 100, 0.10);
  }

  .hero-kicker {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #0b6b6f;
  }
</style>
