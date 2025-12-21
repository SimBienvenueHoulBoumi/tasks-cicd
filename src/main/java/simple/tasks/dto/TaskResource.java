package simple.tasks.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AccessLevel;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;
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

    @Getter(AccessLevel.NONE)
    @Setter(AccessLevel.NONE)
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

    /**
     * Getter défensif pour éviter d'exposer la représentation interne de la Map.
     */
    public Map<String, String> get_links() {
        return _links == null ? null : Map.copyOf(_links);
    }

    /**
     * Setter défensif pour éviter de stocker une Map externe modifiable.
     */
    public void set_links(Map<String, String> links) {
        this._links = links == null ? null : Map.copyOf(links);
    }
}



