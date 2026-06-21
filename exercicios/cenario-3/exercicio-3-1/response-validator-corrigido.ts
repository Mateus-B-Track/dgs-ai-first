import { z } from "zod";
import { logger } from "../shared/logger.js";

export const RagResponseSchema = z
  .object({
    answer: z.string().min(1, "answer não pode ser vazia"),
    source_document: z
      .string()
      .trim()
      .min(1, "source_document não pode ser vazio"),
    confidence_score: z
      .number()
      .min(0, "confidence_score deve ser >= 0")
      .max(1, "confidence_score deve ser <= 1"),
  })
  .strict();

export type RagResponse = z.infer<typeof RagResponseSchema>;

export interface FallbackResponse {
  answer: string;
  source_document: "";
  confidence_score: 0;
}

const FALLBACK_RESPONSE: Readonly<FallbackResponse> = Object.freeze({
  answer:
    "Não foi possível gerar uma resposta confiável. Por favor, consulte um supervisor.",
  source_document: "",
  confidence_score: 0,
});

const DANGEROUS_CARGO_PATTERN = /carga\s+perigosa/i;
const RETURN_PATTERN =
  /devolu[çc][ãa]o|devolv(?:er|id[oa]s?)|retorn(?:o|ar)|reversa|enviar\s+de\s+volta|restitu(?:ir|i[çc][ãa]o)/i;

export function validateResponse(raw: unknown): RagResponse | FallbackResponse {
  const result = RagResponseSchema.safeParse(raw);

  if (!result.success) {
    logger.warn(
      { errors: result.error.flatten() },
      "Resposta do modelo falhou na validação do schema",
    );
    return FALLBACK_RESPONSE;
  }

  const response = result.data;

  if (!response.source_document) {
    logger.warn("Resposta rejeitada: source_document vazio ou ausente");
    return FALLBACK_RESPONSE;
  }

  if (
    DANGEROUS_CARGO_PATTERN.test(response.answer) &&
    RETURN_PATTERN.test(response.answer)
  ) {
    logger.warn(
      "Guardrail ativado: resposta menciona devolução e carga perigosa simultaneamente",
    );
    return FALLBACK_RESPONSE;
  }

  return response;
}
