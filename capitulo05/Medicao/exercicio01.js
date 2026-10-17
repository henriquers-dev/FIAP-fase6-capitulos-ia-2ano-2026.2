import React, { useState } from 'react';
import {
   View,
   Text,
   TextInput,
   TouchableOpacity,
   StyleSheet,
   Alert,
   ScrollView
} from 'react-native';
import storage from '../utils/storage';

export default function MedirPressaoScreen({ navigation }) {
   const [sistolica, setSistolica] = useState('');
   const [diastolica, setDiastolica] = useState('');

   const handleSalvar = async () => {
      if (!sistolica || !diastolica) {
         Alert.alert('Atenção', 'Preencha ambos os valores');
         return;
      }

      const agora = new Date();
      const novaMedicao = {
         id: Date.now(),
         sistolica: parseInt(sistolica),
         diastolica: parseInt(diastolica),
         data: agora.toLocaleDateString('pt-BR'),
         hora: agora.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
         }),
      };

      try {
         // Buscar medições existentes
         const medicoesJSON = await storage.getItem('@medicoes');
         const medicoes = medicoesJSON ? JSON.parse(medicoesJSON) : [];

         // Adicionar nova medição no início
         medicoes.unshift(novaMedicao);

         // Salvar de volta
         await storage.setItem('@medicoes', JSON.stringify(medicoes));

         // Limpar campos
         setSistolica('');
         setDiastolica('');

         // Redirecionar para Home
         navigation.navigate('Início');

      } catch (error) {
         console.error('Erro ao salvar medição:', error);
         Alert.alert('Erro', 'Não foi possível salvar a medição');
      }
   };

   // Botão só fica habilitado se ambos os campos estiverem preenchidos
   const botaoHabilitado = sistolica && diastolica;

   return (
      <ScrollView style={styles.container}>
         <View style={styles.content}>
            <Text style={styles.title}>Registrar Medição</Text>
            <Text style={styles.subtitle}>Informe os valores da sua pressão arterial</Text>

            <View style={styles.infoBox}>
               <Text style={styles.infoText}>
                  💡 Meça em repouso, sentado, com o braço apoiado na altura do coração
               </Text>
            </View>

            <View style={styles.inputRow}>
               <View style={styles.inputGroup}>
                  <Text style={styles.label}>Sistólica (máx)</Text>
                  <TextInput
                     style={styles.input}
                     value={sistolica}
                     onChangeText={setSistolica}
                     keyboardType="numeric"
                     maxLength={3}
                  />
                  <Text style={styles.hint}>mmHg</Text>
               </View>

               <Text style={styles.separator}>×</Text>

               <View style={styles.inputGroup}>
                  <Text style={styles.label}>Diastólica (mín)</Text>
                  <TextInput
                     style={styles.input}
                     value={diastolica}
                     onChangeText={setDiastolica}
                     keyboardType="numeric"
                     maxLength={3}
                  />
                  <Text style={styles.hint}>mmHg</Text>
               </View>
            </View>

            <TouchableOpacity
               style={[styles.button, !botaoHabilitado && styles.buttonDisabled]}
               onPress={handleSalvar}
               disabled={!botaoHabilitado}
            >
               <Text style={styles.buttonText}>Salvar Medição</Text>
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
   title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 8,
   },
   subtitle: {
      fontSize: 14,
      color: '#666',
      marginBottom: 20,
   },
   infoBox: {
      backgroundColor: '#f0f0f0',
      padding: 15,
      borderRadius: 8,
      marginBottom: 30,
   },
   infoText: {
      fontSize: 14,
      color: '#555',
      lineHeight: 20,
   },
   inputRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 30,
   },
   inputGroup: {
      flex: 1,
      alignItems: 'center',
   },
   label: {
      fontSize: 12,
      color: '#666',
      marginBottom: 8,
   },
   input: {
      backgroundColor: '#fff',
      borderWidth: 2,
      borderColor: '#E63946',
      borderRadius: 8,
      padding: 15,
      fontSize: 32,
      fontWeight: 'bold',
      textAlign: 'center',
      width: '100%',
      color: '#333',
   },
   hint: {
      fontSize: 12,
      color: '#999',
      marginTop: 4,
   },
   separator: {
      fontSize: 40,
      color: '#ccc',
      marginHorizontal: 15,
      fontWeight: 'bold',
   },
   button: {
      backgroundColor: '#E63946',
      padding: 16,
      borderRadius: 8,
      alignItems: 'center',
   },
   buttonDisabled: {
      backgroundColor: '#ccc',
   },
   buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
   },
});
