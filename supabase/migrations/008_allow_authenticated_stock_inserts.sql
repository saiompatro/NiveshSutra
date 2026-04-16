CREATE POLICY "Authenticated users can insert stocks"
ON public.stocks
FOR INSERT
TO authenticated
WITH CHECK (true);
