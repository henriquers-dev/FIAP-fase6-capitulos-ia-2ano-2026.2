const usuario = { nome: 'Henrique', email: 'henrique@email.com' };
await AsyncStorage.setItem('@usuario', JSON.stringify(usuario));

const usuarioString = await AsyncStorage.getItem('@usuario');
const usuario = JSON.parse(usuarioString);

const usuario = { nome: 'João', email: 'joao@email.com' };

await AsyncStorage.setItem('@usuario', JSON.stringify(usuario));

const usuario = JSON.parse(usuarioString);
