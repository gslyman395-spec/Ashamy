import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import DashboardScreen from './mobile/DashboardScreen';
import DeveloperModeScreen from './mobile/DeveloperModeScreen';

const SCREENS = {
  dashboard: DashboardScreen,
  developer: DeveloperModeScreen,
};

export default function App() {
  const [activeScreen, setActiveScreen] = useState('dashboard');
  const ActiveScreen = SCREENS[activeScreen];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeScreen === 'dashboard' && styles.tabActive]}
          onPress={() => setActiveScreen('dashboard')}
        >
          <Text style={styles.tabText}>لوحة التحكم</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeScreen === 'developer' && styles.tabActive]}
          onPress={() => setActiveScreen('developer')}
        >
          <Text style={styles.tabText}>وضع المطور</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.screenContainer}>
        <ActiveScreen />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    gap: 8,
    backgroundColor: '#111827',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#1f2937',
  },
  tabActive: {
    backgroundColor: '#00BCD4',
  },
  tabText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  screenContainer: {
    flex: 1,
  },
});
