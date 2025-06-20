package simple.tasks.services;

import main.java.simple.tasks.*;

import main.java.simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;
import org.junit.jupiter.api.Test;


import simple.tasks.services.DeleteTask;

import java.util.Optional;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class DeleteTaskTest {

    private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final DeleteTask service = new DeleteTask(tasksRepository);

    @Test
    void shouldDeleteTaskIfExists() {
        Tasks task = new Tasks("To Delete");
        when(tasksRepository.findById(1L)).thenReturn(Optional.of(task));

        service.deleteTask(1L);
        verify(tasksRepository).delete(task);
    }

    @Test
    void shouldThrowIfTaskNotFound() {
        when(tasksRepository.findById(2L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, () -> service.deleteTask(2L));
    }
}
