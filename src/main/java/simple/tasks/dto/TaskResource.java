package simple.tasks.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import simple.tasks.models.Tasks;

import java.util.Map;

/**
 * DTO de réponse enrichi avec des liens "hypermedia-like" dans le champ _links.
 */
@Data
@Schema(name = "TaskResource", description = "Représente une tâche avec des liens hypermedia")
public class TaskResource {

    @Schema(description = "Identifiant technique de la tâche", example = "1")
    private Long id;

    @Schema(description = "Nom de la tâche", example = "Faire les courses")
    private String name;

    @Schema(
        description = "Liens hypermedia relatifs à cette ressource",
        example = "{\"self\":\"/tasks/1\",\"tasks\":\"/tasks\"}"
    )
    private Map<String, String> _links;

    public TaskResource(Tasks task) {
        this.id = task.getId();
        this.name = task.getName();
        this._links = Map.of(
            "self", "/tasks/" + this.id,
            "tasks", "/tasks"
        );
    }
}



