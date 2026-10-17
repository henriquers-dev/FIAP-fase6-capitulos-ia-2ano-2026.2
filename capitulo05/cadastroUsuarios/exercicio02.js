import { useState } from 'react';
import {
   View,
   Text,
   TextInput,
   TouchableOpacity,
   StyleSheet,
   ScrollView,
   Alert
} from 'react-native';
import storage from '../utils/storage';

export default function CadastroScreen({ navigation }) {
   const [nome, setNome] = useState('');
   const [email, setEmail] = useState('');
   const [senha, setSenha] = useState('');
   const [confirmarSenha, setConfirmarSenha] = useState('');

   const validarEmail = (email) => {
      const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return regex.test(email);
   };

   const handleCadastro = async () => {
      // Validação: campos vazios
      if (!nome || !email || !senha || !confirmarSenha) {
         Alert.alert('Erro', 'Preencha todos os campos');
         return;
      }

      // Validação: nome muito curto
      if (nome.length < 3) {
         Alert.alert('Erro', 'Nome deve ter pelo menos 3 caracteres');
         return;
      }

      // Validação: email inválido
      if (!validarEmail(email)) {
         Alert.alert('Erro', 'Digite um email válido');
         return;
      }

      // Validação: senha muito curta
      if (senha.length < 6) {
         Alert.alert('Erro', 'Senha deve ter pelo menos 6 caracteres');
         return;
      }

      // Validação: senhas não conferem
      if (senha !== confirmarSenha) {
         Alert.alert('Erro', 'As senhas não conferem');
         return;
      }

      try {
         // Buscar usuários existentes
         const usuariosJSON = await storage.getItem('@usuarios');
         const usuarios = usuariosJSON ? JSON.parse(usuariosJSON) : [];

         // Verificar se email já existe
         const emailExiste = usuarios.some(u => u.email === email);
         if (emailExiste) {
            Alert.alert('Erro', 'Este email já está cadastrado');
            return;
         }

         // Criar novo usuário
         const novoUsuario = {
            id: Date.now().toString(),
            nome,
            email: email.toLowerCase(),
            senha,
            dataCadastro: new Date().toISOString()
         };

         // Adicionar à lista e salvar
         usuarios.push(novoUsuario);
         await storage.setItem('@usuarios', JSON.stringify(usuarios));

         Alert.alert('Sucesso', 'Cadastro realizado!', [
            { text: 'OK', onPress: () => navigation.navigate('Login') }
         ]);

         // Limpar campos
         setNome('');
         setEmail('');
         setSenha('');
         setConfirmarSenha('');

      } catch (error) {
         console.error('Erro ao cadastrar:', error);
         Alert.alert('Erro', 'Não foi possível realizar o cadastro');
      }
   };

   return (
      <ScrollView style={styles.container}>
         <View style={styles.content}>
            <Text style={styles.title}>Criar Conta</Text>
            <Text style={styles.subtitle}>Preencha seus dados abaixo</Text>

            <TextInput
               style={styles.input}
               placeholder="Nome completo"
               value={nome}
               onChangeText={setNome}
               autoCapitalize="words"
            />

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

            <TextInput
               style={styles.input}
               placeholder="Confirmar senha"
               value={confirmarSenha}
               onChangeText={setConfirmarSenha}
               secureTextEntry
            />

            <TouchableOpacity style={styles.button} onPress={handleCadastro}>
               <Text style={styles.buttonText}>Cadastrar</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
               <Text style={styles.linkText}>Já tem conta? Faça login</Text>
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
      fontSize: 28,
      fontWeight: 'bold',
      color: '#333',
      marginBottom: 8,
   },
   subtitle: {
      fontSize: 16,
      color: '#666',
      marginBottom: 30,
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
