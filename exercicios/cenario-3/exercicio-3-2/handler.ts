import { app, HttpRequest, HttpResponseInit } from "@azure/functions";
import { CosmosClient } from "@azure/cosmos";
import pino from "pino";
import { z } from "zod";

const logger = pino();

const FeedbackSchema = z.object({
  queryId: z.string(),
  rating: z.number().int().min(1).max(5),
  comment: z.string().optional(),
  attendantEmail: z.string().email(),
});

const connectionString = process.env.COSMOS_CONNECTION_STRING;
if (!connectionString) {
  throw new Error(
    "Variável de ambiente COSMOS_CONNECTION_STRING não configurada.",
  );
}

const client = new CosmosClient(connectionString);
const container = client.database("novatech").container("feedbacks");

export async function feedbackHandler(
  request: HttpRequest,
): Promise<HttpResponseInit> {
  const body: unknown = await request.json().catch(() => null);

  if (!body) {
    return {
      status: 400,
      jsonBody: { error: "Request body inválido ou ausente." },
    };
  }

  const parsed = FeedbackSchema.safeParse(body);

  if (!parsed.success) {
    logger.warn(
      { errors: parsed.error.flatten().fieldErrors },
      "Validação de feedback falhou",
    );
    return {
      status: 400,
      jsonBody: {
        error: "Validação falhou.",
        details: parsed.error.flatten().fieldErrors,
      },
    };
  }

  const feedback = {
    queryId: parsed.data.queryId,
    rating: parsed.data.rating,
    comment: parsed.data.comment,
    attendantEmail: parsed.data.attendantEmail,
    timestamp: new Date().toISOString(),
  };

  try {
    await container.items.create(feedback);
  } catch (err: unknown) {
    logger.error(
      { queryId: feedback.queryId, err },
      "Erro ao salvar feedback no Cosmos DB",
    );
    return {
      status: 500,
      jsonBody: { error: "Erro interno ao salvar feedback." },
    };
  }

  logger.info(
    { queryId: feedback.queryId, rating: feedback.rating },
    "Feedback salvo com sucesso",
  );

  return { status: 201, jsonBody: { message: "Feedback criado com sucesso." } };
}

app.http("feedback", {
  methods: ["POST"],
  handler: feedbackHandler,
});
