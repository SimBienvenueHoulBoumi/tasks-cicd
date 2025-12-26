package simple.tasks.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import simple.tasks.models.Tasks;

import java.util.Map;

/**
 * DTO de réponse enrichi avec des liens "hypermedia-like" dans le champ _links.
 */
@Schema(name = "TaskResource", description = "Représente une tâche avec des liens hypermedia")
public record TaskResource(

    @Schema(description = "Identifiant technique de la tâche", example = "1")
    Long id,

    @Schema(description = "Nom de la tâche", example = "Faire les courses")
    String name,

    @JsonProperty("_links")
    @Schema(
        description = "Liens hypermedia relatifs à cette ressource",
        example = "{\"self\":\"/tasks/1\",\"tasks\":\"/tasks\"}"
    )
    Map<String, String> links
) {

    /**
     * Constructeur de confort depuis l'entité de domaine {@link Tasks}.
     */
    public TaskResource(Tasks task) {
        this(
            task.getId(),
            task.getName(),
            Map.of(
                "self", "/tasks/" + task.getId(),
                "tasks", "/tasks"
            )
        );
    }

    /**
     * Accesseur défensif pour éviter d'exposer la représentation interne de la Map.
     */
    @Override
    public Map<String, String> links() {
        return links == null ? null : Map.copyOf(links);
    }
}



