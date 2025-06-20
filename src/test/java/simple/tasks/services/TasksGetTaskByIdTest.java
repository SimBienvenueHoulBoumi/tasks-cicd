package simple.tasks.services;

import simple.tasks.exceptions.ResourceNotFoundException;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class TasksGetTaskByIdTest {

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
