import { z } from "zod";
import { logger } from "../shared/logger.js";

export const RagResponseSchema = z
  .object({
    answer: z.string().min(1, "answer não pode ser vazia"),
    source_document: z.string().min(1, "source_document não pode ser vazio"),
    confidence_score: z
      .number()
      .min(0, "confidence_score deve ser >= 0")
      .max(1, "confidence_score deve ser <= 1"),
  })
  .strict();

export type RagResponse = z.infer<typeof RagResponseSchema>;

const FALLBACK_RESPONSE: RagResponse = {
  answer:
    "Não foi possível gerar uma resposta confiável. Por favor, consulte um supervisor.",
  source_document: "",
  confidence_score: 0,
};

const DANGEROUS_CARGO_PATTERN = /carga\s+perigosa/i;
const RETURN_PATTERN = /devolu[çc][ãa]o|devolver|devolvida/i;
const NEGATION_PATTERN = /\bnão\b|impossível|proibido|vedado|não é possível/i;

export function validateResponse(raw: unknown): RagResponse {
  const result = RagResponseSchema.safeParse(raw);

  if (!result.success) {
    logger.warn(
      { errors: result.error.flatten() },
      "Resposta do modelo falhou na validação do schema",
    );
    return FALLBACK_RESPONSE;
  }

  const response = result.data;

  if (!response.source_document.trim()) {
    logger.warn("Resposta rejeitada: source_document vazio ou ausente");
    return FALLBACK_RESPONSE;
  }

  if (
    DANGEROUS_CARGO_PATTERN.test(response.answer) &&
    RETURN_PATTERN.test(response.answer) &&
    !NEGATION_PATTERN.test(response.answer)
  ) {
    logger.warn(
      "Guardrail ativado: modelo afirmou devolução de carga perigosa sem negativa",
    );
    return FALLBACK_RESPONSE;
  }

  return response;
}
