package com.javadcs;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.Arrays;
import java.util.List;


public class TacviewClient
{

    public static void main(String[] args) throws Exception
    {
        new Client().run();
        // Thread clientThread = new Thread(new Client());
        // clientThread.start();
    }

    private static class Client implements Runnable
    {

        @Override
        public void run()
        {
            List<String> handshake_params = Arrays.asList(
                                   "XtraLib.Stream.0",
                                   "Tacview.RealTimeTelemetry.0",
                                   "tacview_reader",
                                   "0"
              );
            String handshake = String.join("\n", handshake_params);

            Socket socket = null;
            PrintWriter out = null;
            BufferedReader in = null;
            BufferedReader read = new BufferedReader(new InputStreamReader(System.in));
            try
            {
                socket = new Socket("127.0.0.1", 5555);
                // socket = new Socket("147.135.8.169", 42674); # Gaw
                out = new PrintWriter(socket.getOutputStream(), true);
                in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                debug("Connected");

                // textToServer = read.readLine();
                debug("Sending '" + handshake + "'");
                out.print(handshake + "\0"); // send to server
                out.flush();

                String obj = null;
                while ((obj = in.readLine()) != null)
                    debug(obj); // read from server and print it.

                out.close();
                in.close();
                read.close();
                socket.close();
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }
        }
    }

    private static void debug(String msg)
    {
        System.out.println("Client: " + msg);
    }
}
