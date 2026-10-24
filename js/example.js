import AgentRouter from "./index.js";

const client = new AgentRouter({
  apiKey: process.env.AGENTROUTER_API_KEY || "sk-***",
});

async function run() {
  console.log("=== 1. Basic Chat (Node.js) ===");
  const reply = await client.chat("Explain P/E ratio in one sentence.", {
    model: "gpt-6-astra",
  });
  console.log(reply);

  console.log("\n=== 2. Streaming (Node.js) ===");
  for await (const chunk of client.stream("Count from 1 to 5.", { model: "gpt-6-astra" })) {
    process.stdout.write(chunk);
  }
  console.log("\n");

  console.log("=== 3. Multi-turn Conversation (Node.js) ===");
  const chat = client.conversation({ model: "gpt-6-astra" });
  const turn1 = await chat.send("My favorite color is green.");
  console.log("Turn 1:", turn1.text);
  const turn2 = await chat.send("What is my favorite color?");
  console.log("Turn 2:", turn2.text);
}

run().catch(console.error);
