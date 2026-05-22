import { writable } from 'svelte/store';

const DEFAULT_API_BASE_URL = 'https://sayidj-web-skripsi-fathur.hf.space';
// const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';

const API_BASE_URL_STORAGE_KEY = 'apiBaseUrl';

function normalizeUrl(value) {
  return value?.trim().replace(/\/+$/, '') || DEFAULT_API_BASE_URL;
}

function getInitialApiBaseUrl() {
  if (typeof localStorage === 'undefined') {
    return DEFAULT_API_BASE_URL;
  }

  return normalizeUrl(localStorage.getItem(API_BASE_URL_STORAGE_KEY));
}

export const apiBaseUrl = writable(getInitialApiBaseUrl());

// Store for server stats
export const serverStats = writable(null);

export async function initializeApiUrl() {
  const initialUrl = getInitialApiBaseUrl();
  apiBaseUrl.set(initialUrl);

  try {
    localStorage.setItem(API_BASE_URL_STORAGE_KEY, initialUrl);
  } catch (error) {
    console.error('Could not persist API base URL locally:', error);
  }
}

export function setApiBaseUrl(value) {
  const normalizedUrl = normalizeUrl(value);
  apiBaseUrl.set(normalizedUrl);

  try {
    localStorage.setItem(API_BASE_URL_STORAGE_KEY, normalizedUrl);
  } catch (error) {
    console.error('Could not persist API base URL locally:', error);
  }
}
