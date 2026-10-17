import { useState } from 'react';
import {
   View,
   Text,
   TextInput,
   TouchableOpacity,
   StyleSheet,
   Alert
} from 'react-native';
import storage from '../utils/storage';

export default function LoginScreen({ navigation }) {
   const [email, setEmail] = useState('');
   const [senha, setSenha] = useState('');

   const handleLogin = async () => {
      if (!email || !senha) {
         Alert.alert('Erro', 'Preencha email e senha');
         return;
      }

      try {
         // Buscar usuários cadastrados
         const usuariosJSON = await storage.getItem('@usuarios');
         const usuarios = usuariosJSON ? JSON.parse(usuariosJSON) : [];

         // Buscar usuário por email e senha
         const usuario = usuarios.find(
            u => u.email === email.toLowerCase() && u.senha === senha
         );

         if (usuario) {
            // Login bem-sucedido - salvar sessão
            await storage.setItem('@usuario_logado', JSON.stringify(usuario));

            // Navegação será automática (App.js detecta mudança)
         } else {
            Alert.alert('Erro', 'Email ou senha incorretos');
         }
      } catch (error) {
         console.error('Erro ao fazer login:', error);
         Alert.alert('Erro', 'Não foi possível fazer login');
      }
   };

   return (
      <View style={styles.container}>
         <Text style={styles.title}>Bem-vindo!</Text>
         <Text style={styles.subtitle}>Faça login para continuar</Text>

         <TextInput
            style={styles.input}
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
         />

         <TextInput
            style={styles.input}
            placeholder="Senha"
            value={senha}
            onChangeText={setSenha}
            secureTextEntry
         />

         <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>Entrar</Text>
         </TouchableOpacity>

         <TouchableOpacity onPress={() => navigation.navigate('Cadastro')}>
            <Text style={styles.linkText}>Não tem conta? Cadastre-se</Text>
         </TouchableOpacity>
      </View>
   );
}

const styles = StyleSheet.create({
   container: {
      flex: 1,
      justifyContent: 'center',
      padding: 20,
      backgroundColor: '#f5f5f5',
   },
   title: {
      fontSize: 32,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 8,
   },
   subtitle: {
      fontSize: 16,
      color: '#666',
      marginBottom: 40,
   },
   input: {
      backgroundColor: '#fff',
      padding: 15,
      borderRadius: 8,
      fontSize: 16,
      marginBottom: 15,
      borderWidth: 1,
      borderColor: '#ddd',
   },
   button: {
      backgroundColor: '#E63946',
      padding: 16,
      borderRadius: 8,
      alignItems: 'center',
      marginTop: 10,
   },
   buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
   },
   linkText: {
      color: '#E63946',
      textAlign: 'center',
      marginTop: 20,
      fontSize: 14,
   },
});
