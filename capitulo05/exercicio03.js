import AsyncStorage from '@react-native-async-storage/async-storage';

const storage = {
  async getItem(key) {
    try {
      // Tentar usar AsyncStorage primeiro (mobile)
      const value = await AsyncStorage.getItem(key);

      // Se não encontrou e estamos na web, tentar localStorage
      if (value === null && typeof window !== 'undefined' && window.localStorage) {
        const localValue = window.localStorage.getItem(key);
        return localValue;
      }

      return value;
    } catch (error) {
      console.error(`[Storage] Erro ao buscar ${key}:`, error);

      // Fallback para localStorage na web
      if (typeof window !== 'undefined' && window.localStorage) {
        try {
          const localValue = window.localStorage.getItem(key);
          return localValue;
        } catch (localError) {
          console.error(`[Storage] Erro no fallback localStorage:`, localError);
        }
      }

      return null;
    }
  },

  async setItem(key, value) {
    try {
      // Salvar no AsyncStorage
      await AsyncStorage.setItem(key, value);

      // Também salvar no localStorage se estiver na web
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, value);

        // Disparar evento customizado para notificar mudança
        window.dispatchEvent(new StorageEvent('storage', {
          key: key,
          oldValue: null,
          newValue: value,
          url: window.location.href
        }));
      }
    } catch (error) {
      console.error(`[Storage] Erro ao salvar ${key}:`, error);
      throw error;
    }
  },

  async removeItem(key) {
    try {
      await AsyncStorage.removeItem(key);

      // Também remover do localStorage se estiver na web
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(key);

        // Disparar evento customizado
        window.dispatchEvent(new StorageEvent('storage', {
          key: key,
          oldValue: null,
          newValue: null,
          url: window.location.href
        }));
      }
    } catch (error) {
      console.error(`[Storage] Erro ao remover ${key}:`, error);
    }
  },

  async clear() {
    try {
      await AsyncStorage.clear();

      // Também limpar localStorage se estiver na web
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.clear();
      }
    } catch (error) {
      console.error(`[Storage] Erro ao limpar:`, error);
    }
  }
};

export default storage;
