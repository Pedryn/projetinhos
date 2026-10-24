import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, Alert, Linking, StyleSheet } from "react-native";

const WhatsAppMessageSender = () => {
  const [numero, setNumero] = useState("");
  const [nome, setNome] = useState("");
  const [item, setItem] = useState("");
  const [mensagemPadrao, setMensagemPadrao] = useState(
    "Olá {nome}, estamos com uma entrega sua de {item} que será entregue hoje. Tem alguém para receber?"
  );

  const enviarMensagem = () => {
    if (!numero || !nome || !item) {
      Alert.alert("Erro", "Preencha todos os campos!");
      return;
    }

    const mensagem = mensagemPadrao
      .replace("{nome}", nome)
      .replace("{item}", item);

    const url = `https://wa.me/55${numero}?text=${encodeURIComponent(mensagem)}`;

    Linking.openURL(url).catch(() => {
      Alert.alert("Erro", "Não foi possível abrir o WhatsApp");
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Mensagem Padrão:</Text>
      <Text style={styles.infoText}>
        Para modificar a mensagem, use <Text style={styles.bold}>{`{nome}`}</Text> para o nome e <Text style={styles.bold}>{`{item}`}</Text> para o item a ser entregue.
      </Text>
      <TextInput
        placeholder="Escreva sua mensagem..."
        value={mensagemPadrao}
        onChangeText={setMensagemPadrao}
        style={styles.inputMultiline}
        multiline
      />

      <TextInput
        placeholder="Número (DDD + número)"
        keyboardType="numeric"
        value={numero}
        onChangeText={setNumero}
        style={styles.input}
        placeholderTextColor="#888"
      />
      <TextInput
        placeholder="Nome do cliente"
        value={nome}
        onChangeText={setNome}
        style={styles.input}
        placeholderTextColor="#888"
      />
      <TextInput
        placeholder="Item a ser entregue"
        value={item}
        onChangeText={setItem}
        style={styles.input}
        placeholderTextColor="#888"
      />

      <TouchableOpacity style={styles.button} onPress={enviarMensagem}>
        <Text style={styles.buttonText}>Enviar Mensagem</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#f5f5f5",
    justifyContent: "center",
  },
  label: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 5,
    color: "#333",
  },
  infoText: {
    fontSize: 16,
    color: "#555",
    marginBottom: 10,
  },
  bold: {
    fontWeight: "bold",
    fontSize: 17,
    color: "#333",
  },
  input: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 10,
    fontSize: 17,
    borderWidth: 1,
    borderColor: "#ccc",
    marginBottom: 15,
  },
  inputMultiline: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 10,
    fontSize: 17,
    borderWidth: 1,
    borderColor: "#ccc",
    marginBottom: 15,
    height: 80,
    textAlignVertical: "top",
  },
  button: {
    backgroundColor: "#25D366",
    padding: 18,
    borderRadius: 10,
    alignItems: "center",
  },
  buttonText: {
    fontSize: 19,
    fontWeight: "bold",
    color: "#fff",
  },
});

export default WhatsAppMessageSender;
