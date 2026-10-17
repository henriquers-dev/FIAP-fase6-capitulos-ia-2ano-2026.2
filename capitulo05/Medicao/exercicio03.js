import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import MedicaoCard from '../components/MedicaoCard';
import LoadingSpinner from '../components/LoadingSpinner';
import storage from '../utils/storage';

export default function HomeScreen() {
   const [carregando, setCarregando] = useState(true);
   const [medicoes, setMedicoes] = useState([]);

   const carregarMedicoes = async () => {
      try {
         const medicoesJSON = await storage.getItem('@medicoes');
         const medicoes = medicoesJSON ? JSON.parse(medicoesJSON) : [];
         setMedicoes(medicoes);
      } catch (error) {
         console.error('Erro ao carregar medições:', error);
      } finally {
         setCarregando(false);
      }
   };
   // Recarrega toda vez que a tela ganha foco
   useFocusEffect(
      useCallback(() => {
         carregarMedicoes();
      }, [])
   );

   if (carregando) {
      return <LoadingSpinner message="Carregando medições..." />;
   }

   return (
      <ScrollView style={styles.container}>
         <View style={styles.content}>
            <Text style={styles.header}>Histórico de Medições</Text>
            <Text style={styles.subtitle}>
               {medicoes.length > 0
                  ? `${medicoes.length} medição(ões) registrada(s)`
                  : 'Nenhuma medição registrada ainda'}
            </Text>

            {medicoes.length === 0 ? (
               <View style={styles.emptyState}>
                  <Text style={styles.emptyIcon}>📊</Text>
                  <Text style={styles.emptyText}>
                     Comece registrando sua primeira medição na aba "Medir Pressão"
                  </Text>
               </View>
            ) : (
               medicoes.map(medicao => (
                  <MedicaoCard
                     key={medicao.id}
                     sistolica={medicao.sistolica}
                     diastolica={medicao.diastolica}
                     data={medicao.data}
                     hora={medicao.hora}
                  />
               ))
            )}
         </View>
      </ScrollView>
   );
}

const styles = StyleSheet.create({
   container: {
      flex: 1,
      backgroundColor: '#f5f5f5'
   },
   content: {
      padding: 20
   },
   header: {
      fontSize: 24,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 5,
   },
   subtitle: {
      fontSize: 14,
      color: '#666',
      marginBottom: 20,
   },
   emptyState: {
      alignItems: 'center',
      paddingVertical: 60,
   },
   emptyIcon: {
      fontSize: 64,
      marginBottom: 16,
   },
   emptyText: {
      fontSize: 16,
      color: '#999',
      textAlign: 'center',
      paddingHorizontal: 40,
   },
});
