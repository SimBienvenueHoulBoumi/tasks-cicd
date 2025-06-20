package simple.tasks.services;

import java.util.Optional;

import services.TasksGetTaskById;

import exceptions.ResourceNotFoundException;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;
import services.TasksGetTaskById;

public class TasksGetTaskByIdTest {
     private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final TasksGetTaskById service = new TasksGetTaskById(tasksRepository);

    @Test
    void shouldReturnTaskIfExists() {
        Tasks task = new Tasks("Test Task");
        when(tasksRepository.findById(1L)).thenReturn(Optional.of(task));

        Tasks result = service.getTaskById(1L);
        assertEquals("Test Task", result.getName());
    }

    @Test
    void shouldThrowIfTaskNotFound() {
        when(tasksRepository.findById(2L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> service.getTaskById(2L));
    }
}
