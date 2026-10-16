import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  Alert
} from 'react-native';

const CLOUD_API_URL = "http://10.0.2.2:8000"; // Android Emulator loopback or local LAN IP

interface Device {
  device_id: string;
  device_name: string;
  status: string;
  device_type: string;
}

interface TaskStep {
  tool_name: string;
  action_description: string;
  verified: boolean;
}

interface Task {
  task_id: string;
  command: string;
  target_device_id: string;
  status: string;
  result_summary?: string;
  steps?: TaskStep[];
}

export default function App() {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("laptop_win_01");
  const [commandText, setCommandText] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loginAndSync();
  }, []);

  const loginAndSync = async () => {
    try {
      setLoading(true);
      // Authenticate as mobile client
      const loginRes = await fetch(`${CLOUD_API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "siva",
          password: "password123",
          device_id: "phone_android_01"
        })
      });

      if (!loginRes.ok) throw new Error("Auth failed");
      const authData = await loginRes.json();
      setAuthToken(authData.access_token);

      // Register mobile device
      await fetch(`${CLOUD_API_URL}/api/v1/devices/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authData.access_token}`
        },
        body: JSON.stringify({
          device_id: "phone_android_01",
          user_id: authData.user_id,
          device_name: "Siva's Android Phone",
          device_type: "ANDROID",
          os_version: "Android 14",
          status: "ONLINE",
          capabilities: ["voice_input", "remote_dispatch", "push_notifications"]
        })
      });

      // Fetch paired devices (including Windows Laptop)
      const devRes = await fetch(`${CLOUD_API_URL}/api/v1/devices`, {
        headers: { "Authorization": `Bearer ${authData.access_token}` }
      });
      const devData = await devRes.json();
      setDevices(devData.devices || []);
    } catch (e: any) {
      console.warn("Mobile sync error:", e.message);
    } finally {
      setLoading(false);
    }
  };

  const dispatchRemoteTask = async () => {
    if (!commandText.trim()) return;
    if (!authToken) {
      Alert.alert("Authentication Error", "Please wait for cloud synchronization.");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${CLOUD_API_URL}/api/v1/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({
          command: commandText.trim(),
          target_device_id: selectedDevice
        })
      });

      if (!res.ok) throw new Error("Failed to dispatch task");
      const newTask = await res.json();
      setTasks(prev => [newTask, ...prev]);
      setCommandText("");

      // Poll task for verified completion
      pollTask(newTask.task_id);
    } catch (e: any) {
      Alert.alert("Dispatch Failed", e.message);
    } finally {
      setLoading(false);
    }
  };

  const pollTask = async (taskId: string) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      if (attempts > 15) clearInterval(interval);

      try {
        const res = await fetch(`${CLOUD_API_URL}/api/v1/tasks/${taskId}`, {
          headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.ok) {
          const updated = await res.json();
          setTasks(prev => prev.map(t => t.task_id === taskId ? updated : t));
          if (updated.status === "COMPLETED" || updated.status === "FAILED") {
            clearInterval(interval);
          }
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080b14" />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoOrb} />
        <View>
          <Text style={styles.headerTitle}>JARVIS MOBILE</Text>
          <Text style={styles.headerSubtitle}>Cross-Device Operator</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Device Fleet Selector */}
        <Text style={styles.sectionTitle}>TARGET EXECUTION DEVICE</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.deviceRow}>
          <TouchableOpacity
            style={[styles.deviceChip, selectedDevice === 'laptop_win_01' && styles.deviceChipActive]}
            onPress={() => setSelectedDevice('laptop_win_01')}
          >
            <Text style={styles.deviceIcon}>💻</Text>
            <Text style={styles.deviceChipTitle}>Windows Laptop</Text>
            <Text style={styles.deviceChipMeta}>Host (Online)</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.deviceChip, selectedDevice === 'local' && styles.deviceChipActive]}
            onPress={() => setSelectedDevice('local')}
          >
            <Text style={styles.deviceIcon}>📱</Text>
            <Text style={styles.deviceChipTitle}>This Phone</Text>
            <Text style={styles.deviceChipMeta}>Local Device</Text>
          </TouchableOpacity>
        </ScrollView>

        {/* Remote Command Input */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>DISPATCH REMOTE INSTRUCTION</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Open VS Code on my laptop and run my Python assignment..."
            placeholderTextColor="#4f5f7a"
            value={commandText}
            onChangeText={setCommandText}
            multiline
          />
          <TouchableOpacity
            style={styles.actionButton}
            onPress={dispatchRemoteTask}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#080b14" />
            ) : (
              <Text style={styles.actionButtonText}>Dispatch to Laptop ➔</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Live Tasks List */}
        <Text style={styles.sectionTitle}>TASK SYNC & VERIFICATION</Text>
        {tasks.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No remote tasks submitted yet.</Text>
          </View>
        ) : (
          tasks.map(t => (
            <View key={t.task_id} style={[styles.card, styles.taskCard]}>
              <View style={styles.taskHeader}>
                <Text style={styles.taskCommand}>{t.command}</Text>
                <View style={[styles.statusBadge, t.status === 'COMPLETED' ? styles.statusCompleted : styles.statusRunning]}>
                  <Text style={styles.statusText}>{t.status}</Text>
                </View>
              </View>
              <Text style={styles.taskId}>Target: {t.target_device_id} • ID: {t.task_id}</Text>
              {t.result_summary ? (
                <View style={styles.summaryBox}>
                  <Text style={styles.summaryText}>✓ Verified: {t.result_summary}</Text>
                </View>
              ) : null}
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080b14',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 240, 255, 0.15)',
    backgroundColor: '#0d1224',
  },
  logoOrb: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#00f0ff',
    marginRight: 12,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ffffff',
    letterSpacing: 1.5,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#8b9bb4',
    letterSpacing: 0.8,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#00f0ff',
    letterSpacing: 1.2,
    marginVertical: 12,
  },
  deviceRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  deviceChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 12,
    marginRight: 10,
    minWidth: 140,
  },
  deviceChipActive: {
    borderColor: '#00f0ff',
    backgroundColor: 'rgba(0, 240, 255, 0.08)',
  },
  deviceIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  deviceChipTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  deviceChipMeta: {
    color: '#8b9bb4',
    fontSize: 10,
    marginTop: 2,
  },
  card: {
    backgroundColor: 'rgba(16, 23, 44, 0.75)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.12)',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#8b9bb4',
    letterSpacing: 1,
    marginBottom: 10,
  },
  input: {
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 10,
    color: '#ffffff',
    padding: 12,
    fontSize: 14,
    minHeight: 70,
    textAlignVertical: 'top',
    marginBottom: 12,
  },
  actionButton: {
    backgroundColor: '#00f0ff',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonText: {
    color: '#080b14',
    fontSize: 14,
    fontWeight: '700',
  },
  taskCard: {
    marginBottom: 12,
  },
  taskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  taskCommand: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusRunning: {
    backgroundColor: 'rgba(0, 240, 255, 0.15)',
  },
  statusCompleted: {
    backgroundColor: 'rgba(0, 255, 136, 0.15)',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#00ff88',
  },
  taskId: {
    color: '#4f5f7a',
    fontSize: 11,
    marginTop: 6,
    fontFamily: 'monospace',
  },
  summaryBox: {
    marginTop: 10,
    padding: 8,
    borderRadius: 6,
    backgroundColor: 'rgba(0, 255, 136, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: '#00ff88',
  },
  summaryText: {
    color: '#d4edda',
    fontSize: 12,
    lineHeight: 16,
  },
  emptyContainer: {
    padding: 30,
    alignItems: 'center',
  },
  emptyText: {
    color: '#4f5f7a',
    fontSize: 13,
  },
});
