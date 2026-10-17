// Criar novo usuário
const novoUsuario = {
   id: Date.now().toString(),
   nome,
   email: email.toLowerCase(),
   senha,
   dataCadastro: new Date().toISOString()
};
