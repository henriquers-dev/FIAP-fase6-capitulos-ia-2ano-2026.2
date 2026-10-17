// Verificar se email já existe
const emailExiste = usuarios.some(u => u.email === email);
if (emailExiste) {
   Alert.alert('Erro', 'Este email já está cadastrado');
   return;
}
