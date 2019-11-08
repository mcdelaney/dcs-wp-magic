package com.javadcs;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.Date;
import java.util.Arrays;
import java.util.List;


public class TacviewClient
{
    public static void main (String[] args)
    {
        try
        {
            TacviewClient tacview = new TacviewClient();
            tacview.run(args);
        }
        catch (Exception e)
        {
            e.printStackTrace ();
        }
    }

    private void run(String[] args) throws Exception
        {
            String host = "127.0.0.1";
            int port = 5555;
            int max_iter = 100;

            if (args.length >= 3 && args[0].equals("host"))
                host = args[1];


            if (args.length >= 3 && args[2].equals("port"))
                port = Integer.parseInt(args[3]);


            if (args.length >= 5 && args[4].equals("max_iter"))
                max_iter = Integer.parseInt(args[5]);


            debug("Connecting to host: " + host);
            debug("Connecting on port: " + port);
            debug("Maximum iterations to run: " + max_iter);

            List<String> handshake_params = Arrays.asList(
                                   "XtraLib.Stream.0",
                                   "Tacview.RealTimeTelemetry.0",
                                   "tacview_reader",
                                   "0"
              );
            String handshake = String.join("\n", handshake_params);

            Socket socket;
            PrintWriter out;
            BufferedReader in;
            BufferedReader read = new BufferedReader(new InputStreamReader(System.in));
            try
            {
                socket = new Socket(host, port);
                // socket = new Socket("147.135.8.169", 42674); # Gaw
                out = new PrintWriter(socket.getOutputStream(), true);
                in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                debug("Connected");

                // textToServer = read.readLine();
                debug("Sending '" + handshake + "'");
                out.print(handshake + "\0"); // send to server
                out.flush();

                long start_time = new Date().getTime();

                int total_iter = 0;

                String obj;
                while (total_iter < max_iter & ((obj = in.readLine()) != null))
                {
                    total_iter++;
                    debug(obj);
                }

                long end_time = new Date().getTime();
                float time_diff = (int) ((end_time - start_time));
                float iter_per_sec = (total_iter/time_diff) * 1000;

                debug("Total lines read:: " + total_iter);
                debug("Time diff: " + time_diff);
                debug("Lines per second:: " + iter_per_sec );

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
//    }

    private static void debug(String msg)
    {
        System.out.println("Client: " + msg);
    }
}


