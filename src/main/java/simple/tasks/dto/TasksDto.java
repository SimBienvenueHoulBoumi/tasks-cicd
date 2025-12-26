package simple.tasks.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * DTO immuable utilisé comme payload pour créer ou mettre à jour une tâche.
 * <p>
 * Utilise un {@code record} Java plutôt que Lombok pour plus de lisibilité
 * et pour éviter le code généré "invisible" pour Sonar / les outils d'analyse.
 */
@Schema(name = "TaskRequest", description = "Payload pour créer ou mettre à jour une tâche")
public record TasksDto(

    @Schema(description = "Nom de la tâche", example = "Faire les courses")
    String name
) {
}

