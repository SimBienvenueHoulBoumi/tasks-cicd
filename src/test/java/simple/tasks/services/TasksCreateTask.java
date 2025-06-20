package simple.tasks.services;

import services.TasksCreateTask;
import dto.TasksDto;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;
import org.junit.jupiter.api.Test;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class TasksCreateTaskTest {

    private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final TasksCreateTask service = new TasksCreateTask(tasksRepository);

    @Test
    void shouldCreateNewTask() {
        TasksDto dto = new TasksDto("New Task");
        Tasks newTask = new Tasks(dto.getName());

        when(tasksRepository.save(any(Tasks.class))).thenReturn(newTask);

        Tasks result = service.createTask(dto);

        assertNotNull(result);
        assertEquals("New Task", result.getName());
        verify(tasksRepository).save(any(Tasks.class));
    }
}
