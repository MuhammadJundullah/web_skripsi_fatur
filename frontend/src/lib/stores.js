// update
import { writable } from 'svelte/store';

// Default API base URL, will be overwritten by initialization
export const apiBaseUrl = writable('https://sayidj-web-skripsi-fathur.hf.space');

// Store for server stats
export const serverStats = writable(null);

// Function to initialize the apiBaseUrl from the backend
export async function initializeApiUrl() {
  const defaultUrl = 'https://sayidj-web-skripsi-fathur.hf.space';
  try {
    const response = await fetch(`${defaultUrl}/settings/api_base_url`);
    if (response.ok) {
      const data = await response.json();
      apiBaseUrl.set(data.value);
      console.log("Loaded API Base URL from DB:", data.value);
    } else {
      // If not found, set the default one in the DB for next time
      await fetch(`${defaultUrl}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'api_base_url', value: defaultUrl })
      });
      console.log("Initialized default API Base URL in DB.");
    }
  } catch (error) {
    console.error("Could not fetch API base URL from settings, using default:", error);
  }
}
