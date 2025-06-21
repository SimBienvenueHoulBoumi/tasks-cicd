package simple.tasks.dto;
import lombok.Data;

@Data
public class TasksDto {
    public TasksDto(String name) {
        this.name = name;
    }
    private Long id;
    private String name;
}
