/**
 * KAOS SDK POC — Demostración de integración con @opencode-ai/sdk
 * 
 * Uso: npx tsx .tools/sdk-poc.ts
 * Nota: Requiere npm install @opencode-ai/sdk en KAOS/.opencode/
 */
import { createOpencode, createOpencodeClient } from "@opencode-ai/sdk"

async function main() {
  console.log("🚀 KAOS SDK POC — Iniciando...")

  // Opción 1: Crear instancia de opencode (servidor + cliente)
  try {
    const { client, server } = await createOpencode({
      hostname: "127.0.0.1",
      port: 4096,
    })

    // Health check
    const health = await client.global.health()
    console.log(`✅ Server health: ${health.data.healthy} (v${health.data.version})`)

    // Listar agentes disponibles
    const agents = await client.app.agents()
    console.log(`✅ Agents disponibles: ${agents.data.map((a: any) => a.name).join(", ")}`)

    // Crear sesión
    const session = await client.session.create({
      body: { title: "SDK POC - Quality Check" },
    })
    console.log(`✅ Sesión creada: ${session.data.id}`)

    // Enviar prompt con structured output
    const result = await client.session.prompt({
      path: { id: session.data.id },
      body: {
        model: { providerID: "antigravity", modelID: "claude-sonnet-4-6" },
        parts: [{ type: "text", text: "Evalúa la calidad del sistema KAOS en 3 líneas" }],
      },
    })
    console.log(`✅ Respuesta: ${result.data.info?.text?.slice(0, 200)}...`)

    // Cerrar servidor
    server.close()
    console.log("✅ SDK POC completado exitosamente")
  } catch (error) {
    console.error("❌ Error en SDK POC:", error instanceof Error ? error.message : error)
    console.log("   (Es normal si opencode no está corriendo — instalar con: npm install @opencode-ai/sdk)")
  }
}

main()
