import { Platform } from 'react-native';

const DEFAULT_BASE_URL = `http://${Platform.select({
  android: '10.0.2.2',
  default: 'localhost',
})}:8000`;

const overrideUrl =
  typeof process !== 'undefined' && process.env
    ? process.env.EXPO_PUBLIC_API_BASE_URL
    : undefined;

export const BASE_URL = (overrideUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
export const API_URL = `${BASE_URL}/api/v1`;
export const WS_URL = `${BASE_URL.replace(/^http/, 'ws')}/ws/signals`;
