<script>
  import { apiBaseUrl, setApiBaseUrl } from './stores.js';
  import { onMount } from 'svelte';

  let currentApiUrl = $apiBaseUrl;
  let status = '';
  let unsubscribe = () => {};

  onMount(() => {
    unsubscribe = apiBaseUrl.subscribe(value => {
      currentApiUrl = value;
    });

    return () => unsubscribe();
  });

  async function saveSettings() {
    status = 'Menyimpan...';
    try {
      setApiBaseUrl(currentApiUrl);
      status = 'Berhasil disimpan.';
    } catch (error) {
      status = `Error: ${error.message}`;
      console.error(error);
    } finally {
      setTimeout(() => status = '', 3000);
    }
  }
</script>

<div class="card">
  <div class="card-body">
    <h5 class="card-title">Konfigurasi API</h5>
    <div class="row g-2 align-items-end">
      <div class="col">
        <label for="api-url" class="form-label">Base URL Backend</label>
        <input id="api-url" type="text" class="form-control" bind:value={currentApiUrl} />
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" on:click={saveSettings}>Simpan</button>
      </div>
    </div>
    {#if status}
      <div class="form-text">{status}</div>
    {/if}
    <div class="form-text">Default backend: `https://sayidj-web-skripsi-fathur.hf.space`.</div>
  </div>
</div>
