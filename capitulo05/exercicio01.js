await AsyncStorage.setItem('@chave', 'valor');

const valor = await AsyncStorage.getItem('@chave');
await AsyncStorage.clear();
