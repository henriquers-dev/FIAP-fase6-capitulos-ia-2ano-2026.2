import React, { useState, useCallback } from 'react';
import {
   View,
   Text,
   StyleSheet,
   ScrollView,
   TouchableOpacity,
   Alert
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import storage from '../utils/storage';

export default function ProfileScreen({ navigation }) {
   const [usuario, setUsuario] = useState(null);
   const [estatisticas, setEstatisticas] = useState(null);

   const carregarDados = async () => {
      try {
         const usuarioJSON = await storage.getItem('@usuario_logado');
         const usuario = usuarioJSON ? JSON.parse(usuarioJSON) : null;
         setUsuario(usuario);

         const medicoesJSON = await storage.getItem('@medicoes');
         const medicoes = medicoesJSON ? JSON.parse(medicoesJSON) : [];

         if (medicoes.length > 0) {
            setEstatisticas(calcularEstatisticas(medicoes));
         }
      } catch (error) {
         console.error('Erro ao carregar dados:', error);
      }
   };

   const calcularEstatisticas = (medicoes) => {
      const totalMedicoes = medicoes.length;

      const mediaSistolica = Math.round(
         medicoes.reduce((acc, m) => acc + m.sistolica, 0) / totalMedicoes
      );

      const mediaDiastolica = Math.round(
         medicoes.reduce((acc, m) => acc + m.diastolica, 0) / totalMedicoes
      );

      return {
         totalMedicoes,
         mediaSistolica,
         mediaDiastolica,
      };
   };

   useFocusEffect(
      useCallback(() => {
         carregarDados();
      }, [])
   );

   const handleLogout = async () => {
      try {
         await storage.removeItem('@usuario_logado');

         if (typeof window !== 'undefined' && window.localStorage) {
            window.localStorage.removeItem('@usuario_logado');
         }

         setUsuario(null);
      } catch (error) {
         console.error('[Profile] Erro ao fazer logout:', error);
      }
   };

   if (!usuario) {
      return null;
   }

   return (
      <ScrollView style={styles.container}>
         <View style={styles.content}>
            <View style={styles.header}>
               <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                     {usuario.nome.charAt(0).toUpperCase()}
                  </Text>
               </View>
               <Text style={styles.nome}>{usuario.nome}</Text>
               <Text style={styles.email}>{usuario.email}</Text>
            </View>

            {estatisticas && (
               <View style={styles.statsContainer}>
                  <Text style={styles.statsTitle}>Estatísticas</Text>

                  <View style={styles.statBox}>
                     <Text style={styles.statLabel}>Total de Medições</Text>
                     <Text style={styles.statValue}>{estatisticas.totalMedicoes}</Text>
                  </View>

                  <View style={styles.statBox}>
                     <Text style={styles.statLabel}>Média Sistólica</Text>
                     <Text style={styles.statValue}>{estatisticas.mediaSistolica} mmHg</Text>
                  </View>

                  <View style={styles.statBox}>
                     <Text style={styles.statLabel}>Média Diastólica</Text>
                     <Text style={styles.statValue}>{estatisticas.mediaDiastolica} mmHg</Text>
                  </View>
               </View>
            )}

            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
               <Text style={styles.logoutText}>Sair da Conta</Text>
            </TouchableOpacity>
         </View>
      </ScrollView>
   );
}

const styles = StyleSheet.create({
   container: {
      flex: 1,
      backgroundColor: '#f5f5f5',
   },
   content: {
      padding: 20,
   },
   header: {
      alignItems: 'center',
      marginBottom: 30,
   },
   avatar: {
      width: 80,
      height: 80,
      borderRadius: 40,
      backgroundColor: '#5856D6',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: 15,
   },
   avatarText: {
      fontSize: 32,
      color: '#fff',
      fontWeight: 'bold',
   },
   nome: {
      fontSize: 24,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 5,
   },
   email: {
      fontSize: 14,
      color: '#666',
   },
   statsContainer: {
      backgroundColor: '#fff',
      borderRadius: 12,
      padding: 20,
      marginBottom: 20,
   },
   statsTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 15,
   },
   statBox: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: '#f0f0f0',
   },
   statLabel: {
      fontSize: 14,
      color: '#666',
   },
   statValue: {
      fontSize: 14,
      fontWeight: 'bold',
      color: '#333',
   },
   logoutButton: {
      backgroundColor: '#E63946',
      padding: 16,
      borderRadius: 8,
      alignItems: 'center',
      marginTop: 20,
   },
   logoutText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
   },
});
