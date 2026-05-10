import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

public class InspectGephiClass {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Usage: InspectGephiClass <fqcn> [fqcn...]");
            return;
        }

        for (String className : args) {
            System.out.println("=== " + className + " ===");
            Class<?> cls = Class.forName(className);

            System.out.println("Constructors:");
            for (Constructor<?> ctor : cls.getDeclaredConstructors()) {
                System.out.println("  " + Modifier.toString(ctor.getModifiers()) + " " + ctor.toGenericString());
            }

            System.out.println("Methods:");
            for (Method method : cls.getDeclaredMethods()) {
                System.out.println("  " + Modifier.toString(method.getModifiers()) + " " + method.toGenericString());
            }
            System.out.println();
        }
    }
}
