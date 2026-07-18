import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'react-native';
import DashboardScreen from './DashboardScreen';
import DeveloperModeScreen from './DeveloperModeScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#1a1a2e',
            borderTopColor: '#00BCD4',
            borderTopWidth: 1,
          },
          tabBarActiveTintColor: '#00BCD4',
          tabBarInactiveTintColor: '#666',
        }}
      >
        <Tab.Screen
          name="Dashboard"
          component={DashboardScreen}
          options={{ tabBarLabel: '📊 لوحة التحكم' }}
        />
        <Tab.Screen
          name="Developer"
          component={DeveloperModeScreen}
          options={{ tabBarLabel: '🛠️ المطور' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
