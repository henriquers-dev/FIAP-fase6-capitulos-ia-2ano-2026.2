usuarios.push(novoUsuario);
await storage.setItem('@usuarios', JSON.stringify(usuarios));
