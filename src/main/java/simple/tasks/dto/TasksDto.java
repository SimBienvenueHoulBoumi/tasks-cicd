package simple.tasks.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@Schema(name = "TaskRequest", description = "Payload pour créer ou mettre à jour une tâche")
public class TasksDto {

    @Schema(description = "Nom de la tâche", example = "Faire les courses", required = true)
    private String name;

    public TasksDto(String name) {
        this.name = name;
    }
}

