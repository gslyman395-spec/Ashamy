import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  StatusBar,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { WebSocket } from 'react-native';

const screenWidth = Dimensions.get('window').width;

export default function DashboardScreen() {
  const [stocks, setStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState('NVDA');
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [accuracy, setAccuracy] = useState(94.2);
  const [webSocket, setWebSocket] = useState(null);

  // API Base URL
  const API_URL = 'http://localhost:8000/api/v1';

  // تحميل البيانات
  useEffect(() => {
    fetchDashboardData();
    connectWebSocket();
    
    return () => {
      if (webSocket) {
        webSocket.close();
      }
    };
  }, []);

  // الاتصال بـ WebSocket
  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/signals');
      
      ws.onopen = () => {
        console.log('✅ WebSocket Connected');
      };
      
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'signal_update') {
          updateStockData(data);
        }
      };
      
      ws.onerror = (error) => {
        console.log('❌ WebSocket Error:', error);
      };
      
      setWebSocket(ws);
    } catch (error) {
      console.log('WebSocket connection failed:', error);
    }
  };

  // جلب بيانات لوحة التحكم
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // جلب الأسهم الشهيرة
      const response = await fetch(`${API_URL}/leaderboard`);
      const data = await response.json();
      setStocks(data.top_gainers || []);
      
      // جلب بيانات السهم المختار
      fetchStockSignal(selectedStock);
      
      // حفظ البيانات محلياً
      await AsyncStorage.setItem('dashboard_data', JSON.stringify(data));
    } catch (error) {
      console.log('Error fetching dashboard:', error);
      // تحميل البيانات المحفوظة إذا فشل الاتصال
      loadCachedData();
    } finally {
      setLoading(false);
    }
  };

  // جلب إشارة السهم
  const fetchStockSignal = async (symbol) => {
    try {
      const response = await fetch(`${API_URL}/signals/${symbol}?timeframes=1D,4H`);
      const data = await response.json();
      setStockData(data);
      
      if (data.final_confidence) {
        setAccuracy(Math.round(data.final_confidence * 100) / 100);
      }
      
      await AsyncStorage.setItem(`stock_${symbol}`, JSON.stringify(data));
    } catch (error) {
      console.log('Error fetching stock signal:', error);
    }
  };

  // تحديث بيانات السهم من WebSocket
  const updateStockData = (data) => {
    if (data.symbol === selectedStock) {
      setStockData(data);
      setAccuracy(data.final_confidence * 100);
    }
  };

  // تحميل البيانات المحفوظة
  const loadCachedData = async () => {
    try {
      const cached = await AsyncStorage.getItem('dashboard_data');
      if (cached) {
        const data = JSON.parse(cached);
        setStocks(data.top_gainers || []);
      }
    } catch (error) {
      console.log('Error loading cached data:', error);
    }
  };

  // تحديث يدوي
  const onRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  // تغيير السهم المختار
  const handleStockSelect = (symbol) => {
    setSelectedStock(symbol);
    fetchStockSignal(symbol);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        style={styles.scrollView}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🚀 Ashamy</Text>
          <Text style={styles.headerSubtitle}>تحليل الأسهم بالذكاء الاصطناعي</Text>
        </View>

        {/* AI Accuracy */}
        <View style={styles.accuracyCard}>
          <Text style={styles.accuracyLabel}>دقة AI الحالية</Text>
          <Text style={styles.accuracyValue}>{accuracy}%</Text>
          <View style={styles.accuracyBar}>
            <View
              style={[
                styles.accuracyFill,
                { width: `${accuracy}%` },
              ]}
            />
          </View>
          <Text style={styles.accuracyStatus}>
            {accuracy >= 90 ? '✅ ممتاز' : accuracy >= 80 ? '✓ جيد' : '⚠️ يحتاج تحسين'}
          </Text>
        </View>

        {/* Selected Stock Analysis */}
        {stockData && (
          <View style={styles.signalCard}>
            <View style={styles.signalHeader}>
              <Text style={styles.signalSymbol}>{selectedStock}</Text>
              <View
                style={[
                  styles.signalBadge,
                  {
                    backgroundColor:
                      stockData.direction === 'BUY' ? '#4CAF50' : '#f44336',
                  },
                ]}
              >
                <Text style={styles.signalBadgeText}>
                  {stockData.direction || 'HOLD'}
                </Text>
              </View>
            </View>

            <View style={styles.signalDetails}>
              <View style={styles.signalRow}>
                <Text style={styles.signalLabel}>السعر الحالي:</Text>
                <Text style={styles.signalValue}>
                  ${stockData.entry_price || 'N/A'}
                </Text>
              </View>
              <View style={styles.signalRow}>
                <Text style={styles.signalLabel}>السعر الهدف:</Text>
                <Text style={styles.signalValue}>
                  ${stockData.target_price || 'N/A'}
                </Text>
              </View>
              <View style={styles.signalRow}>
                <Text style={styles.signalLabel}>نقطة الايقاف:</Text>
                <Text style={styles.signalValue}>
                  ${stockData.stop_loss || 'N/A'}
                </Text>
              </View>
              <View style={styles.signalRow}>
                <Text style={styles.signalLabel}>الثقة:</Text>
                <Text style={[styles.signalValue, { color: '#FFD700' }]}>
                  {Math.round(stockData.final_confidence * 100)}%
                </Text>
              </View>
              <View style={styles.signalRow}>
                <Text style={styles.signalLabel}>التقييم:</Text>
                <Text style={styles.signalValue}>
                  {'⭐'.repeat(stockData.stars || 0)}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Loading */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#00BCD4" />
            <Text style={styles.loadingText}>جاري التحميل...</Text>
          </View>
        )}

        {/* Top Stocks */}
        <View style={styles.stocksContainer}>
          <Text style={styles.sectionTitle}>أفضل الأسهم اليوم</Text>
          {stocks.slice(0, 5).map((stock, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.stockItem,
                selectedStock === stock.symbol && styles.stockItemActive,
              ]}
              onPress={() => handleStockSelect(stock.symbol)}
            >
              <View style={styles.stockInfo}>
                <Text style={styles.stockName}>{stock.symbol}</Text>
                <Text style={styles.stockPrice}>${stock.price}</Text>
              </View>
              <View
                style={[
                  styles.stockChange,
                  { backgroundColor: stock.change >= 0 ? '#4CAF50' : '#f44336' },
                ]}
              >
                <Text style={styles.stockChangeText}>
                  {stock.change >= 0 ? '+' : ''}{stock.change}%
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* AI Models Status */}
        <View style={styles.modelsContainer}>
          <Text style={styles.sectionTitle}>حالة نماذج AI</Text>
          {[
            { name: 'LSTM', accuracy: 92.4 },
            { name: 'GRU', accuracy: 91.8 },
            { name: 'Transformer', accuracy: 93.1 },
            { name: 'Ensemble', accuracy: 92.7 },
          ].map((model, index) => (
            <View key={index} style={styles.modelItem}>
              <Text style={styles.modelName}>{model.name}</Text>
              <View style={styles.modelBar}>
                <View
                  style={[
                    styles.modelFill,
                    { width: `${model.accuracy}%` },
                  ]}
                />
              </View>
              <Text style={styles.modelAccuracy}>{model.accuracy}%</Text>
            </View>
          ))}
        </View>

        {/* Settings */}
        <View style={styles.settingsContainer}>
          <TouchableOpacity style={styles.settingsButton}>
            <Text style={styles.settingsButtonText}>⚙️ الإعدادات</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.settingsButton}>
            <Text style={styles.settingsButtonText}>📊 المحفظة</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.settingsButton}>
            <Text style={styles.settingsButtonText}>🔔 التنبيهات</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    backgroundColor: '#1a1a2e',
    borderBottomWidth: 1,
    borderBottomColor: '#00BCD4',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00BCD4',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 5,
  },
  accuracyCard: {
    margin: 15,
    padding: 20,
    backgroundColor: '#1a1a2e',
    borderRadius: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#FFD700',
  },
  accuracyLabel: {
    fontSize: 14,
    color: '#999',
    marginBottom: 10,
  },
  accuracyValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 10,
  },
  accuracyBar: {
    height: 10,
    backgroundColor: '#333',
    borderRadius: 5,
    overflow: 'hidden',
    marginBottom: 10,
  },
  accuracyFill: {
    height: '100%',
    backgroundColor: '#FFD700',
  },
  accuracyStatus: {
    fontSize: 12,
    color: '#4CAF50',
    textAlign: 'center',
  },
  signalCard: {
    margin: 15,
    padding: 20,
    backgroundColor: '#1a1a2e',
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#00BCD4',
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  signalSymbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00BCD4',
  },
  signalBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  signalBadgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  signalDetails: {
    gap: 10,
  },
  signalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  signalLabel: {
    color: '#999',
    fontSize: 14,
  },
  signalValue: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  stocksContainer: {
    margin: 15,
    padding: 15,
    backgroundColor: '#1a1a2e',
    borderRadius: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  stockItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 15,
    marginBottom: 10,
    backgroundColor: '#0f0f1e',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#333',
  },
  stockItemActive: {
    borderColor: '#00BCD4',
    backgroundColor: '#1a1a2e',
  },
  stockInfo: {
    flex: 1,
  },
  stockName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  stockPrice: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  stockChange: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  stockChangeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  modelsContainer: {
    margin: 15,
    padding: 15,
    backgroundColor: '#1a1a2e',
    borderRadius: 15,
  },
  modelItem: {
    marginBottom: 15,
  },
  modelName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  modelBar: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
  },
  modelFill: {
    height: '100%',
    backgroundColor: '#00BCD4',
  },
  modelAccuracy: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
    textAlign: 'right',
  },
  settingsContainer: {
    flexDirection: 'row',
    margin: 15,
    gap: 10,
  },
  settingsButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 15,
    backgroundColor: '#1a1a2e',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#00BCD4',
    alignItems: 'center',
  },
  settingsButtonText: {
    color: '#00BCD4',
    fontWeight: 'bold',
    fontSize: 12,
  },
  loadingContainer: {
    marginVertical: 30,
    alignItems: 'center',
  },
  loadingText: {
    color: '#999',
    marginTop: 10,
  },
});
