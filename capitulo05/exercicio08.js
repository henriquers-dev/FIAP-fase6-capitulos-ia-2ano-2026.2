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
