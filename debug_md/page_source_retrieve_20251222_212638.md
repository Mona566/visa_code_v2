# Retrieve Application Page HTML Source

**Timestamp**: 2025-12-22 21:26:38

**URL**: https://www.visas.inis.gov.ie/AVATS/RetrieveApplication.aspx

**Page Title**: AVATS

---

## Full HTML Source

```html
<html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Expires" content="0"><meta http-equiv="Cache-Control" content="no-cache"><meta http-equiv="Pragma" content="no-cache"><title>
	AVATS
</title><link href="CSS/Departmental.css" rel="stylesheet" type="text/css"><link rel="STYLESHEET" type="text/css" href="CSS/popcalendar.css">
    <script language="javascript" src="js/popcalendar.js" type="text/javascript"></script></head><body><div onclick="bShow=true" id="calendar" class="div-style" style="visibility: hidden;"><table width="230" class="table-style" border="0" style="border-collapse:collapse"><tbody><tr class="topnav"><td><table width="228"><tbody><tr><td class="title-style"><b><span id="caption"><span id="spanLeft" class="title-control-normal-style" onmouseover="swapImage(&quot;changeLeft&quot;,&quot;calprev2.gif&quot;);this.className=&quot;title-control-select-style&quot;;window.status=&quot;Click to scroll to previous month. Hold mouse button to scroll automatically.&quot;" onclick="javascript:decMonth()" onmouseout="clearInterval(intervalID1);swapImage(&quot;changeLeft&quot;,&quot;calprev.gif&quot;);this.className=&quot;title-control-normal-style&quot;;window.status=&quot;&quot;" onmousedown="clearTimeout(timeoutID1);timeoutID1=setTimeout(&quot;StartDecMonth()&quot;,500)" onmouseup="clearTimeout(timeoutID1);clearInterval(intervalID1)">&nbsp;<img id="changeLeft" src="images/calprev.gif" border="0">&nbsp;</span>&nbsp;<span id="spanRight" class="title-control-normal-style" onmouseover="swapImage(&quot;changeRight&quot;,&quot;calnext2.gif&quot;);this.className=&quot;title-control-select-style&quot;;window.status=&quot;Click to scroll to next month. Hold mouse button to scroll automatically.&quot;" onmouseout="clearInterval(intervalID1);swapImage(&quot;changeRight&quot;,&quot;calnext.gif&quot;);this.className=&quot;title-control-normal-style&quot;;window.status=&quot;&quot;" onclick="incMonth()" onmousedown="clearTimeout(timeoutID1);timeoutID1=setTimeout(&quot;StartIncMonth()&quot;,500)" onmouseup="clearTimeout(timeoutID1);clearInterval(intervalID1)">&nbsp;<img id="changeRight" src="images/calnext.gif" border="0">&nbsp;</span>&nbsp;<span id="spanMonth" class="title-control-normal-style" onmouseover="swapImage(&quot;changeMonth&quot;,&quot;drop2.gif&quot;);this.className=&quot;title-control-select-style&quot;;window.status=&quot;Click to select a month.&quot;" onmouseout="swapImage(&quot;changeMonth&quot;,&quot;drop1.gif&quot;);this.className=&quot;title-control-normal-style&quot;;window.status=&quot;&quot;" onclick="popUpMonth()"></span>&nbsp;<span id="spanYear" class="title-control-normal-style" onmouseover="swapImage(&quot;changeYear&quot;,&quot;drop2.gif&quot;);this.className=&quot;title-control-select-style&quot;;window.status=&quot;Click to select a year.&quot;" onmouseout="swapImage(&quot;changeYear&quot;,&quot;drop1.gif&quot;);this.className=&quot;title-control-normal-style&quot;;window.status=&quot;&quot;" onclick="popUpYear()"></span>&nbsp;</span></b></td><td align="right"><a href="javascript:hideCalendar()"><img src="images/close.gif" border="0" alt="Close the Calendar"></a></td></tr></tbody></table></td></tr><tr><td class="body-style"><span id="content"></span></td></tr><tr class="calfooter"><td><span id="lblToday" class="calfooter">Today is <a class="calfooter" onmousemove="window.status=&quot;Go To Current Month&quot;" onmouseout="window.status=&quot;&quot;" title="Go To Current Month" href="javascript:monthSelected=monthNow;yearSelected=yearNow;constructCalendar();">Mon, 22 Dec	2025</a></span></td></tr></tbody></table></div><div id="selectMonth" class="div-style"></div><div id="selectYear" class="div-style"></div>
    <script language="javascript" src="js/common.js" type="text/javascript"></script>
    <link rel="icon" href="favicon.ico" type="image/x-icon">

    <form name="aspnetForm" method="post" action="./RetrieveApplication.aspx" onsubmit="javascript:return WebForm_OnSubmit();" id="aspnetForm">
<div>
<input type="hidden" name="__EVENTTARGET" id="__EVENTTARGET" value="">
<input type="hidden" name="__EVENTARGUMENT" id="__EVENTARGUMENT" value="">
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="/wEPDwULLTIwNDA0ODAzNDMPZBYCZg9kFgICAw9kFgICDw9kFgwCAQ8PFgIeBFRleHRlZGQCCw8QZBAV4gEKLS1TZWxlY3QtLQtBZmdoYW5pc3RhbgdBbGJhbmlhB0FsZ2VyaWEHQW5kb3JyYQZBbmdvbGEIQW5ndWlsbGETQW50aWd1YSBhbmQgQmFyYnVkYQlBcmdlbnRpbmEHQXJtZW5pYQVBcnViYQlBdXN0cmFsaWEHQXVzdHJpYQpBemVyYmFpamFuB0JhaGFtYXMHQmFocmFpbgpCYW5nbGFkZXNoCEJhcmJhZG9zB0JlbGFydXMHQmVsZ2l1bQZCZWxpemUFQmVuaW4HQmVybXVkYQZCaHV0YW4HQm9saXZpYRtCb25haXJlLCBTdCBFdXN0YXRpdXMsIFNhYmEWQm9zbmlhIGFuZCBIZXJ6ZWdvdmluYQhCb3Rzd2FuYQZCcmF6aWwRQnJ1bmVpIERhcnVzc2FsYW0IQnVsZ2FyaWEMQnVya2luYSBGYXNvB0J1cnVuZGkIQ2FtYm9kaWEIQ2FtZXJvb24GQ2FuYWRhCkNhcGUgVmVyZGUOQ2F5bWFuIElzbGFuZHMYQ2VudHJhbCBBZnJpY2FuIFJlcHVibGljBENoYWQFQ2hpbGUIQ29sb21iaWEHQ29tb3JvcwVDb25nbxxDb25nbyBEZW1vY3JhdGljIFJlcHVibGljIG9mCkNvc3RhIFJpY2EbQ290ZSBEJ0l2b2lyZSAoSXZvcnkgQ29hc3QpEkNyb2F0aWEgKEhydmF0c2thKQRDdWJhB0N1cmFjYW8GQ3lwcnVzDkN6ZWNoIFJlcHVibGljB0Rlbm1hcmsIRGppYm91dGkIRG9taW5pY2ESRG9taW5pY2FuIFJlcHVibGljB0VjdWFkb3IFRWd5cHQLRWwgU2FsdmFkb3IRRXF1YXRvcmlhbCBHdWluZWEHRXJpdHJlYQdFc3RvbmlhCEVzd2F0aW5pCEV0aGlvcGlhG0ZhbGtsYW5kIElzbGFuZHMgKE1hbHZpbmFzKQ1GYXJvZSBJc2xhbmRzBEZpamkHRmlubGFuZAZGcmFuY2UFR2Fib24GR2FtYmlhB0dlb3JnaWEHR2VybWFueQVHaGFuYQlHaWJyYWx0YXImR3JlYXQgQnJpdGFpbiAoVUspIC0gRGVwZW5kZW50IENpdGl6ZW4oR3JlYXQgQnJpdGFpbiAoVUspIC0gTmF0aW9uYWwgKG92ZXJzZWFzKSVHcmVhdCBCcml0YWluIChVSykgLSBPdmVyc2VhcyBjaXRpemVuJUdyZWF0IEJyaXRhaW4gKFVLKSAtIFByb3RlY3RlZCBQZXJzb24cR3JlYXQgQnJpdGFpbiAoVUspIC0gU3ViamVjdAZHcmVlY2UJR3JlZW5sYW5kB0dyZW5hZGEJR3VhdGVtYWxhBkd1aW5lYQ1HdWluZWEtQmlzc2F1Bkd1eWFuYQVIYWl0aQhIb2x5IFNlZQhIb25kdXJhcw9Ib25nIEtvbmcgKFNBUikHSHVuZ2FyeQdJY2VsYW5kBUluZGlhCUluZG9uZXNpYQRJcmFuBElyYXEHSXJlbGFuZAZJc3JhZWwFSXRhbHkHSmFtYWljYQVKYXBhbgZKb3JkYW4KS2F6YWtoc3RhbgVLZW55YQhLaXJpYmF0aQ1Lb3JlYSAoTm9ydGgpDUtvcmVhIChTb3V0aCkGS29zb3ZvBkt1d2FpdApLeXJneXpzdGFuBExhb3MGTGF0dmlhB0xlYmFub24HTGVzb3RobwdMaWJlcmlhBUxpYnlhDUxpZWNodGVuc3RlaW4JTGl0aHVhbmlhCkx1eGVtYm91cmcLTWFjYXUgKFNBUikKTWFkYWdhc2NhcgZNYWxhd2kITWFsYXlzaWEITWFsZGl2ZXMETWFsaQVNYWx0YRBNYXJzaGFsbCBJc2xhbmRzCk1hcnRpbmlxdWUKTWF1cml0YW5pYQlNYXVyaXRpdXMGTWV4aWNvCk1pY3JvbmVzaWEHTW9sZG92YQZNb25hY28ITW9uZ29saWEKTW9udGVuZWdybwpNb250c2VycmF0B01vcm9jY28KTW96YW1iaXF1ZQdNeWFubWFyB05hbWliaWEFTmF1cnUFTmVwYWwXTmV0aGVybGFuZHMsIEtpbmdkb20gb2YLTmV3IFplYWxhbmQJTmljYXJhZ3VhBU5pZ2VyB05pZ2VyaWEcTm9ydGggTWFjZWRvbmlhLCBSZXB1YmxpYyBvZgZOb3J3YXkET21hbghQYWtpc3RhbgVQYWxhdR5QYWxlc3RpbmlhbiBOYXRpb25hbCBBdXRob3JpdHkGUGFuYW1hEFBhcHVhIE5ldyBHdWluZWEIUGFyYWd1YXkaUGVvcGxlJ3MgUmVwdWJsaWMgb2YgQ2hpbmEEUGVydQtQaGlsaXBwaW5lcwhQaXRjYWlybgZQb2xhbmQIUG9ydHVnYWwLUHVlcnRvIFJpY28FUWF0YXIHUm9tYW5pYRJSdXNzaWFuIEZlZGVyYXRpb24GUndhbmRhFVNhaW50IEtpdHRzIGFuZCBOZXZpcwtTYWludCBMdWNpYSBTYWludCBWaW5jZW50IGFuZCB0aGUgR3JlbmFkaW5lcwVTYW1vYQpTYW4gTWFyaW5vFVNhbyBUb21lIGFuZCBQcmluY2lwZQxTYXVkaSBBcmFiaWEHU2VuZWdhbAZTZXJiaWEKU2V5Y2hlbGxlcwxTaWVycmEgTGVvbmUJU2luZ2Fwb3JlDFNpbnQgTWFhcnRlbghTbG92YWtpYQhTbG92ZW5pYQ9Tb2xvbW9uIElzbGFuZHMHU29tYWxpYQxTb3V0aCBBZnJpY2ELU291dGggU3VkYW4FU3BhaW4JU3JpIExhbmthCVN0YXRlbGVzcwVTdWRhbghTdXJpbmFtZQZTd2VkZW4LU3dpdHplcmxhbmQUU3lyaWFuIEFyYWIgUmVwdWJsaWMYVGFpd2FuIFByb3ZpbmNlIG9mIENoaW5hClRhamlraXN0YW4IVGhhaWxhbmQLVGltb3ItTGVzdGUEVG9nbwVUb25nYRNUcmluaWRhZCBhbmQgVG9iYWdvB1R1bmlzaWEHVHVya2l5ZQxUdXJrbWVuaXN0YW4YVHVya3MgYW5kIENhaWNvcyBJc2xhbmRzBlR1dmFsdQZVZ2FuZGEHVWtyYWluZRRVbml0ZWQgQXJhYiBFbWlyYXRlczFVbml0ZWQgS2luZ2RvbSAoR3JlYXQgQnJpdGFpbiAmIE5vcnRoZXJuIElyZWxhbmQpG1VuaXRlZCBSZXB1YmxpYyBvZiBUYW56YW5pYRhVbml0ZWQgU3RhdGVzIG9mIEFtZXJpY2EvVW5pdGVkIFN0YXRlcyBvZiBBbWVyaWNhIE1pbm9yIE91dGx5aW5nIElzbGFuZHMHVXJ1Z3VheQ1VU1NSIChmb3JtZXIpClV6YmVraXN0YW4HVmFudWF0dQlWZW5lenVlbGEIVmlldCBOYW0YVmlyZ2luIElzbGFuZHMgKEJyaXRpc2gpFVZpcmdpbiBJc2xhbmRzIChVLlMuKQVZZW1lbgZaYW1iaWEIWmltYmFid2UV4gEBMAEzAzQwOQI1OAExATgBNQE0AjEwATYDNjQ5AjEzAjEyAjE1AjI5AjIyAjE4AjE3AjMzAjE5AjM0AjI0AjI1AjMwAjI3AzY1MgIxNgIzMgIyOAIyNgIyMQIyMAIyMwMxMTECNDMCMzUCNDkDMTE4AjM3AzIwNQI0MgI0NQMxMTMDNTY4AjM4AjQ2AjQwAjk0AjQ4AzY1MQI1MQI1MgI1NQI1NAI1NgI1NwI1OQI2MQMyMDECODQCNjMCNjADMjAzAjY1AjY4AjcwAjY3AjY2AjcxAjczAjgxAjc2AjUzAjc4Ajc5AzU2MQM1NjIDNTYzAzU2NAM1NjUCODUCODACNzUCODcCODICODkCOTACOTUDNTcwAjkzAjkxAjk2AzEwNAMxMDACOTcDMTAzAzEwMgI5OAI5OQMxMDUDMTA2AzEwOAMxMDcDMTE5AzEwOQMxMTIDMTE1AzExNgM2NDMDMTE3AzExMAMxMjADMTI5AzEyMQMxMjYDMTI1AzEzMAMxMjMDMTI3AzEyOAMxNDADMTM0AzE0OAMxNTADMTQ3AzEzNwMxNDUDMTM1AzY0NAMxNDMDMTQ2AzE0OQI2OQMxMzMDMTMyAzEzOQM1MjYDMTQ0AzEzMQMxNTEDNDM1AzE1MgMxNjEDMTYwAzE1OAM1NzUDMTU3AzE1NAMxNTYDMTM2AzE1OQMxNjUDMTcxAzE3NwM1NjYDMTY2AzE2OQMxNzgCNDQDMTY3AzE3MAMxNzQDMTcyAzE3NgM2NDUDMTc5AzE4MQMxODIDMTgzAzExNAMxMjIDMjI4AzIzNQMxOTUDMTk5AzE4NAMxOTYDNTYwAzE4NgMxOTQDMTg5AzY1MAM1NzkDMTkxAzE4NQMxOTcDMjM5AzY0NgI2NAMxMjQDNjQ3AzE4NwMxOTgDMTg4AjM5AzIwMgMyMTgDMjA5AzIwOAMzMTkDMjA3AzIxMwMyMTYDMjEyAzIxNQMyMTEDMjA0AzIxNwMyMjEDMjIwATIDNTc3AzIxOQMzMjIDMjIzAzIyNQMyMDADMjI2AzIzMwMyMjkDMjMyAzIzMAMyMzEDMjM2AzI0MAMyNDIUKwPiAWdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dkZAIPDw8WDB4HRGlzcGxheQsqKlN5c3RlbS5XZWIuVUkuV2ViQ29udHJvbHMuVmFsaWRhdG9yRGlzcGxheQIeCENzc0NsYXNzBRpBcHBsaWNhdGlvbkNsaWVudEVycm9yVGV4dB4MRXJyb3JNZXNzYWdlBSJEYXRlIFJlcXVpcmVkIGluIGRkL21tL3l5eXkgZm9ybWF0HhhDbGllbnRWYWxpZGF0aW9uRnVuY3Rpb24FDkNsZWFyV2F0ZXJNYXJrHhFDb250cm9sVG9WYWxpZGF0ZQUGdHh0RE9CHgRfIVNCAgJkZAIRDw9kFggeB29uZm9jdXMFPmphdmFzY3JpcHQ6Q2xlYXJEYXRlRmllbGQoImN0bDAwX0NvbnRlbnRQbGFjZUhvbGRlcjFfdHh0RE9CIik7HgdvbktleVVwBT9qYXZhc2NyaXB0OkNoZWNrRGF0ZUZvcm1hdCgiY3RsMDBfQ29udGVudFBsYWNlSG9sZGVyMV90eHRET0IiKTseCm9uS2V5UHJlc3MFWGphdmFzY3JpcHQ6cmV0dXJuIERhdGVFeHRlbmRlcigiY3RsMDBfQ29udGVudFBsYWNlSG9sZGVyMV90eHRET0IiLCBldmVudCwgIjEyMzQ1Njc4OTAiKTseBm9uYmx1cgU+amF2YXNjcmlwdDpSZXNldFdhdGVyTWFyaygiY3RsMDBfQ29udGVudFBsYWNlSG9sZGVyMV90eHRET0IiKTtkAhUPDxYCHg5WYWx1ZVRvQ29tcGFyZQUKMjIvMTIvMjAyNWRkAhcPDxYOHwUFBnR4dERPQh8GAgIeBFR5cGULKixTeXN0ZW0uV2ViLlVJLldlYkNvbnRyb2xzLlZhbGlkYXRpb25EYXRhVHlwZQMfAgUaQXBwbGljYXRpb25DbGllbnRFcnJvclRleHQfAwUZUGxlYXNlIGVudGVyIGEgdmFsaWQgZGF0ZR4IT3BlcmF0b3ILKjNTeXN0ZW0uV2ViLlVJLldlYkNvbnRyb2xzLlZhbGlkYXRpb25Db21wYXJlT3BlcmF0b3ICHwsFCjAxLzAxLzE3NTNkZGRWAsVoc2e/lATtzt/whd9pguON9fM+7KuY9QGGc9WB0A==">
</div>

<script type="text/javascript">
//<![CDATA[
var theForm = document.forms['aspnetForm'];
if (!theForm) {
    theForm = document.aspnetForm;
}
function __doPostBack(eventTarget, eventArgument) {
    if (!theForm.onsubmit || (theForm.onsubmit() != false)) {
        theForm.__EVENTTARGET.value = eventTarget;
        theForm.__EVENTARGUMENT.value = eventArgument;
        theForm.submit();
    }
}
//]]>
</script>


<script src="/AVATS/WebResource.axd?d=dgfwUCIUsu7qpB7xWAtu-K4IUBV_v956lpwkj4gR-fvP8QqqEM1eRL3SzyyhJXLbBzHAZlVfOSolxiGVTdBtIpwOHbcIWMKVtAMjXb7eP5E1&amp;t=638901572248157332" type="text/javascript"></script>


<script src="/AVATS/WebResource.axd?d=iT31y_UR78uOdO1rpLySc7WPfaCnrA4gjMxP9-loIC37fPsVF_k_V_u-WVSWQMRDL4-YJ55IvHvwuDTZKI4qe5sT-n9EGAirSodtTMxnVY41&amp;t=638901572248157332" type="text/javascript"></script>
<script type="text/javascript">
//<![CDATA[
function WebForm_OnSubmit() {
if (typeof(ValidatorOnSubmit) == "function" && ValidatorOnSubmit() == false) return false;
return true;
}
//]]>
</script>

<div>

	<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="EDB824C3">
	<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="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">
</div>
    <table width="100%">
        <tbody><tr>
            <td colspan="2">
                <div class="LogoDiv">
                    <img src="Images/justice-logo.png" alt="logo">
                </div>
            </td>
        </tr>
		<tr class="ApplicationButtonBar">
			<td colspan="2">
				
	<table cellpadding="0" cellspacing="0" width="100%">
	<tbody><tr>
        <td>
            <input type="submit" name="ctl00$ButtonBar$btnSubmit" value="Submit" onclick="javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(&quot;ctl00$ButtonBar$btnSubmit&quot;, &quot;&quot;, true, &quot;&quot;, &quot;&quot;, false, false))" id="ctl00_ButtonBar_btnSubmit" class="ApplicationButtons">
        </td>
    </tr>
	</tbody></table>

			</td>
		</tr>
		<tr style="height:600px;">
			<td width="20%" valign="top">
				<table>
					<tbody><tr class="NormalRow">
						<td>
							<a id="ctl00_lnkbtnAppForm" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnAppForm','')">Apply Now</a>
						</td>
					</tr>
					<tr class="AltTableRow">	
						<td>
							<a id="ctl00_lnkbtnRetrieveApp" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnRetrieveApp','')">Retrieve Application</a>
						</td>
					</tr>
					<tr class="NormalRow">
						<td>
							<a id="ctl00_lnkbtnFAQ" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnFAQ','')">Frequently Asked Questions</a>
						</td>
					</tr>
					<tr class="AltTableRow">
						<td>
							<a id="ctl00_lnkbtnTerms" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnTerms','')">Terms &amp; Conditions</a>
						</td>		
					</tr>
					<tr class="NormalRow">
						<td>
							<a id="ctl00_lnkbtnPrivacy" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnPrivacy','')">Privacy Statement &amp; Cookies</a>
						</td>
					</tr>
					<tr class="AltTableRow">
						<td>
							<a id="ctl00_lnkbtnFOI" class="TreeLinksText" href="javascript:__doPostBack('ctl00$lnkbtnFOI','')">Freedom of Information</a>
						</td>		
					</tr>
				</tbody></table>
			</td>
			<td width="80%" valign="top">
				
<table width="100%" cellpadding="2" cellspacing="0">
    <tbody><tr>
        <td colspan="2" class="ApplicationNote">
            If you would like to complete your previous Visa/Preclearance application please provide the following information.
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td></td>
    </tr>
    <tr>
        <td colspan="2" class="ApplicationClientErrorText">
            
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td></td>
    </tr>
    <tr>
        <td colspan="2" class="mandatoryInformation">* Denotes mandatory field</td>
    </tr>
    <tr>
        <td class="LabelText">
            Application Number: <span style="color: red;">*</span>
        </td>
        <td>
            <input name="ctl00$ContentPlaceHolder1$txtTransRecordID" type="text" id="ctl00_ContentPlaceHolder1_txtTransRecordID" class="TextboxText">
            <span id="ctl00_ContentPlaceHolder1_rqfldTransRecNo" title="Please enter application number." class="ApplicationClientErrorText" style="color:Red;display:none;">Please enter application number.</span>
        </td>
    </tr>
    <tr>
        <td class="LabelText">
            Passport Number: <span style="color: red;">*</span>
        </td>
        <td>
            <input name="ctl00$ContentPlaceHolder1$txtPassportNumber" type="text" id="ctl00_ContentPlaceHolder1_txtPassportNumber" class="TextboxText">
            <span id="ctl00_ContentPlaceHolder1_rqfldPassportNo" title="Please enter the passport number." class="ApplicationClientErrorText" style="color:Red;display:none;">Please enter the passport number.</span>
        </td>
    </tr>
    <tr>
        <td class="LabelText">
            Country of Nationality: <span style="color: red;">*</span>
        </td>
        <td>
            <select name="ctl00$ContentPlaceHolder1$ddlNationality" id="ctl00_ContentPlaceHolder1_ddlNationality" class="DropdownListText">
	<option value="0">--Select--</option>
	<option value="3">Afghanistan</option>
	<option value="409">Albania</option>
	<option value="58">Algeria</option>
	<option value="1">Andorra</option>
	<option value="8">Angola</option>
	<option value="5">Anguilla</option>
	<option value="4">Antigua and Barbuda</option>
	<option value="10">Argentina</option>
	<option value="6">Armenia</option>
	<option value="649">Aruba</option>
	<option value="13">Australia</option>
	<option value="12">Austria</option>
	<option value="15">Azerbaijan</option>
	<option value="29">Bahamas</option>
	<option value="22">Bahrain</option>
	<option value="18">Bangladesh</option>
	<option value="17">Barbados</option>
	<option value="33">Belarus</option>
	<option value="19">Belgium</option>
	<option value="34">Belize</option>
	<option value="24">Benin</option>
	<option value="25">Bermuda</option>
	<option value="30">Bhutan</option>
	<option value="27">Bolivia</option>
	<option value="652">Bonaire, St Eustatius, Saba</option>
	<option value="16">Bosnia and Herzegovina</option>
	<option value="32">Botswana</option>
	<option value="28">Brazil</option>
	<option value="26">Brunei Darussalam</option>
	<option value="21">Bulgaria</option>
	<option value="20">Burkina Faso</option>
	<option value="23">Burundi</option>
	<option value="111">Cambodia</option>
	<option value="43">Cameroon</option>
	<option value="35">Canada</option>
	<option value="49">Cape Verde</option>
	<option value="118">Cayman Islands</option>
	<option value="37">Central African Republic</option>
	<option value="205">Chad</option>
	<option value="42">Chile</option>
	<option value="45">Colombia</option>
	<option value="113">Comoros</option>
	<option value="568">Congo</option>
	<option value="38">Congo Democratic Republic of</option>
	<option value="46">Costa Rica</option>
	<option value="40">Cote D'Ivoire (Ivory Coast)</option>
	<option value="94">Croatia (Hrvatska)</option>
	<option value="48">Cuba</option>
	<option value="651">Curacao</option>
	<option value="51">Cyprus</option>
	<option value="52">Czech Republic</option>
	<option value="55">Denmark</option>
	<option value="54">Djibouti</option>
	<option value="56">Dominica</option>
	<option value="57">Dominican Republic</option>
	<option value="59">Ecuador</option>
	<option value="61">Egypt</option>
	<option value="201">El Salvador</option>
	<option value="84">Equatorial Guinea</option>
	<option value="63">Eritrea</option>
	<option value="60">Estonia</option>
	<option value="203">Eswatini</option>
	<option value="65">Ethiopia</option>
	<option value="68">Falkland Islands (Malvinas)</option>
	<option value="70">Faroe Islands</option>
	<option value="67">Fiji</option>
	<option value="66">Finland</option>
	<option value="71">France</option>
	<option value="73">Gabon</option>
	<option value="81">Gambia</option>
	<option value="76">Georgia</option>
	<option value="53">Germany</option>
	<option value="78">Ghana</option>
	<option value="79">Gibraltar</option>
	<option value="561">Great Britain (UK) - Dependent Citizen</option>
	<option value="562">Great Britain (UK) - National (overseas)</option>
	<option value="563">Great Britain (UK) - Overseas citizen</option>
	<option value="564">Great Britain (UK) - Protected Person</option>
	<option value="565">Great Britain (UK) - Subject</option>
	<option value="85">Greece</option>
	<option value="80">Greenland</option>
	<option value="75">Grenada</option>
	<option value="87">Guatemala</option>
	<option value="82">Guinea</option>
	<option value="89">Guinea-Bissau</option>
	<option value="90">Guyana</option>
	<option value="95">Haiti</option>
	<option value="570">Holy See</option>
	<option value="93">Honduras</option>
	<option value="91">Hong Kong (SAR)</option>
	<option value="96">Hungary</option>
	<option value="104">Iceland</option>
	<option value="100">India</option>
	<option value="97">Indonesia</option>
	<option value="103">Iran</option>
	<option value="102">Iraq</option>
	<option value="98">Ireland</option>
	<option value="99">Israel</option>
	<option value="105">Italy</option>
	<option value="106">Jamaica</option>
	<option value="108">Japan</option>
	<option value="107">Jordan</option>
	<option value="119">Kazakhstan</option>
	<option value="109">Kenya</option>
	<option value="112">Kiribati</option>
	<option value="115">Korea (North)</option>
	<option value="116">Korea (South)</option>
	<option value="643">Kosovo</option>
	<option value="117">Kuwait</option>
	<option value="110">Kyrgyzstan</option>
	<option value="120">Laos</option>
	<option value="129">Latvia</option>
	<option value="121">Lebanon</option>
	<option value="126">Lesotho</option>
	<option value="125">Liberia</option>
	<option value="130">Libya</option>
	<option value="123">Liechtenstein</option>
	<option value="127">Lithuania</option>
	<option value="128">Luxembourg</option>
	<option value="140">Macau (SAR)</option>
	<option value="134">Madagascar</option>
	<option value="148">Malawi</option>
	<option value="150">Malaysia</option>
	<option value="147">Maldives</option>
	<option value="137">Mali</option>
	<option value="145">Malta</option>
	<option value="135">Marshall Islands</option>
	<option value="644">Martinique</option>
	<option value="143">Mauritania</option>
	<option value="146">Mauritius</option>
	<option value="149">Mexico</option>
	<option value="69">Micronesia</option>
	<option value="133">Moldova</option>
	<option value="132">Monaco</option>
	<option value="139">Mongolia</option>
	<option value="526">Montenegro</option>
	<option value="144">Montserrat</option>
	<option value="131">Morocco</option>
	<option value="151">Mozambique</option>
	<option value="435">Myanmar</option>
	<option value="152">Namibia</option>
	<option value="161">Nauru</option>
	<option value="160">Nepal</option>
	<option value="158">Netherlands, Kingdom of</option>
	<option value="575">New Zealand</option>
	<option value="157">Nicaragua</option>
	<option value="154">Niger</option>
	<option value="156">Nigeria</option>
	<option value="136">North Macedonia, Republic of</option>
	<option value="159">Norway</option>
	<option value="165">Oman</option>
	<option value="171">Pakistan</option>
	<option value="177">Palau</option>
	<option value="566">Palestinian National Authority</option>
	<option value="166">Panama</option>
	<option value="169">Papua New Guinea</option>
	<option value="178">Paraguay</option>
	<option value="44">People's Republic of China</option>
	<option value="167">Peru</option>
	<option value="170">Philippines</option>
	<option value="174">Pitcairn</option>
	<option value="172">Poland</option>
	<option value="176">Portugal</option>
	<option value="645">Puerto Rico</option>
	<option value="179">Qatar</option>
	<option value="181">Romania</option>
	<option value="182">Russian Federation</option>
	<option value="183">Rwanda</option>
	<option value="114">Saint Kitts and Nevis</option>
	<option value="122">Saint Lucia</option>
	<option value="228">Saint Vincent and the Grenadines</option>
	<option value="235">Samoa</option>
	<option value="195">San Marino</option>
	<option value="199">Sao Tome and Principe</option>
	<option value="184">Saudi Arabia</option>
	<option value="196">Senegal</option>
	<option value="560">Serbia</option>
	<option value="186">Seychelles</option>
	<option value="194">Sierra Leone</option>
	<option value="189">Singapore</option>
	<option value="650">Sint Maarten</option>
	<option value="579">Slovakia</option>
	<option value="191">Slovenia</option>
	<option value="185">Solomon Islands</option>
	<option value="197">Somalia</option>
	<option value="239">South Africa</option>
	<option value="646">South Sudan</option>
	<option value="64">Spain</option>
	<option value="124">Sri Lanka</option>
	<option value="647">Stateless</option>
	<option value="187">Sudan</option>
	<option value="198">Suriname</option>
	<option value="188">Sweden</option>
	<option value="39">Switzerland</option>
	<option value="202">Syrian Arab Republic</option>
	<option value="218">Taiwan Province of China</option>
	<option value="209">Tajikistan</option>
	<option value="208">Thailand</option>
	<option value="319">Timor-Leste</option>
	<option value="207">Togo</option>
	<option value="213">Tonga</option>
	<option value="216">Trinidad and Tobago</option>
	<option value="212">Tunisia</option>
	<option value="215">Turkiye</option>
	<option value="211">Turkmenistan</option>
	<option value="204">Turks and Caicos Islands</option>
	<option value="217">Tuvalu</option>
	<option value="221">Uganda</option>
	<option value="220">Ukraine</option>
	<option value="2">United Arab Emirates</option>
	<option value="577">United Kingdom (Great Britain &amp; Northern Ireland)</option>
	<option value="219">United Republic of Tanzania</option>
	<option value="322">United States of America</option>
	<option value="223">United States of America Minor Outlying Islands</option>
	<option value="225">Uruguay</option>
	<option value="200">USSR (former)</option>
	<option value="226">Uzbekistan</option>
	<option value="233">Vanuatu</option>
	<option value="229">Venezuela</option>
	<option value="232">Viet Nam</option>
	<option value="230">Virgin Islands (British)</option>
	<option value="231">Virgin Islands (U.S.)</option>
	<option value="236">Yemen</option>
	<option value="240">Zambia</option>
	<option value="242">Zimbabwe</option>

</select>
            <span id="ctl00_ContentPlaceHolder1_rqflNationality" title="Please enter country of nationality." class="ApplicationClientErrorText" style="color:Red;display:none;">Please enter country of nationality.</span>
        </td>
    </tr>
    <tr>
        <td class="LabelText" valign="top">
            Date of Birth: <span style="color: red;">*</span>
        </td>
        <td>
            <span id="ctl00_ContentPlaceHolder1_cvtxtDOB" class="ApplicationClientErrorText" style="color:Red;display:none;">Date Required in dd/mm/yyyy format</span>
            <input name="ctl00$ContentPlaceHolder1$txtDOB" type="text" value="dd/mm/yyyy" id="ctl00_ContentPlaceHolder1_txtDOB" class="TextboxText" onfocus="javascript:ClearDateField(&quot;ctl00_ContentPlaceHolder1_txtDOB&quot;);" onkeyup="javascript:CheckDateFormat(&quot;ctl00_ContentPlaceHolder1_txtDOB&quot;);" onkeypress="javascript:return DateExtender(&quot;ctl00_ContentPlaceHolder1_txtDOB&quot;, event, &quot;1234567890&quot;);" onblur="javascript:ResetWaterMark(&quot;ctl00_ContentPlaceHolder1_txtDOB&quot;);">&nbsp;<img src="Images/cal.gif" alt="" onclick="popUpCalendar(this, 'ctl00_ContentPlaceHolder1_txtDOB', 'dd-mm-yyyy')" style="" border="0">
            <span id="ctl00_ContentPlaceHolder1_rqfldDOB" title="Please enter date of birth." class="ApplicationClientErrorText" style="color:Red;display:none;">Please enter date of birth.</span>
            <span id="ctl00_ContentPlaceHolder1_compareValidatorDOB" class="ApplicationClientErrorText" style="color:Red;display:none;">Date of birth must be before current date.</span>
            <br>
            <span id="ctl00_ContentPlaceHolder1_cvMinDOB" class="ApplicationClientErrorText" style="color:Red;display:none;">Please enter a valid date</span>
        </td>
    </tr>
</tbody></table>

			</td>
		</tr>
        <tr id="ctl00_trForBottomButtons" class="ApplicationButtonBar">
	<td colspan="2">
				
	<table cellpadding="0" cellspacing="0" width="100%">
	<tbody><tr>
        <td>
            <input type="submit" name="ctl00$ButtonBarAtBottom$btnSubmitAtBottom" value="Submit" onclick="javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(&quot;ctl00$ButtonBarAtBottom$btnSubmitAtBottom&quot;, &quot;&quot;, true, &quot;&quot;, &quot;&quot;, false, false))" id="ctl00_ButtonBarAtBottom_btnSubmitAtBottom" class="ApplicationButtons">
        </td>
    </tr>
	</tbody></table>

			</td>
</tr>
		
    </tbody></table>
    
<script type="text/javascript">
//<![CDATA[
var Page_Validators =  new Array(document.getElementById("ctl00_ContentPlaceHolder1_rqfldTransRecNo"), document.getElementById("ctl00_ContentPlaceHolder1_rqfldPassportNo"), document.getElementById("ctl00_ContentPlaceHolder1_rqflNationality"), document.getElementById("ctl00_ContentPlaceHolder1_cvtxtDOB"), document.getElementById("ctl00_ContentPlaceHolder1_rqfldDOB"), document.getElementById("ctl00_ContentPlaceHolder1_compareValidatorDOB"), document.getElementById("ctl00_ContentPlaceHolder1_cvMinDOB"));
//]]>
</script>

<script type="text/javascript">
//<![CDATA[
var ctl00_ContentPlaceHolder1_rqfldTransRecNo = document.all ? document.all["ctl00_ContentPlaceHolder1_rqfldTransRecNo"] : document.getElementById("ctl00_ContentPlaceHolder1_rqfldTransRecNo");
ctl00_ContentPlaceHolder1_rqfldTransRecNo.controltovalidate = "ctl00_ContentPlaceHolder1_txtTransRecordID";
ctl00_ContentPlaceHolder1_rqfldTransRecNo.focusOnError = "t";
ctl00_ContentPlaceHolder1_rqfldTransRecNo.errormessage = "Please enter application number.";
ctl00_ContentPlaceHolder1_rqfldTransRecNo.display = "Dynamic";
ctl00_ContentPlaceHolder1_rqfldTransRecNo.evaluationfunction = "RequiredFieldValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_rqfldTransRecNo.initialvalue = "";
var ctl00_ContentPlaceHolder1_rqfldPassportNo = document.all ? document.all["ctl00_ContentPlaceHolder1_rqfldPassportNo"] : document.getElementById("ctl00_ContentPlaceHolder1_rqfldPassportNo");
ctl00_ContentPlaceHolder1_rqfldPassportNo.controltovalidate = "ctl00_ContentPlaceHolder1_txtPassportNumber";
ctl00_ContentPlaceHolder1_rqfldPassportNo.focusOnError = "t";
ctl00_ContentPlaceHolder1_rqfldPassportNo.errormessage = "Please enter the passport number.";
ctl00_ContentPlaceHolder1_rqfldPassportNo.display = "Dynamic";
ctl00_ContentPlaceHolder1_rqfldPassportNo.evaluationfunction = "RequiredFieldValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_rqfldPassportNo.initialvalue = "";
var ctl00_ContentPlaceHolder1_rqflNationality = document.all ? document.all["ctl00_ContentPlaceHolder1_rqflNationality"] : document.getElementById("ctl00_ContentPlaceHolder1_rqflNationality");
ctl00_ContentPlaceHolder1_rqflNationality.controltovalidate = "ctl00_ContentPlaceHolder1_ddlNationality";
ctl00_ContentPlaceHolder1_rqflNationality.focusOnError = "t";
ctl00_ContentPlaceHolder1_rqflNationality.errormessage = "Please enter country of nationality.";
ctl00_ContentPlaceHolder1_rqflNationality.display = "Dynamic";
ctl00_ContentPlaceHolder1_rqflNationality.evaluationfunction = "RequiredFieldValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_rqflNationality.initialvalue = "0";
var ctl00_ContentPlaceHolder1_cvtxtDOB = document.all ? document.all["ctl00_ContentPlaceHolder1_cvtxtDOB"] : document.getElementById("ctl00_ContentPlaceHolder1_cvtxtDOB");
ctl00_ContentPlaceHolder1_cvtxtDOB.controltovalidate = "ctl00_ContentPlaceHolder1_txtDOB";
ctl00_ContentPlaceHolder1_cvtxtDOB.errormessage = "Date Required in dd/mm/yyyy format";
ctl00_ContentPlaceHolder1_cvtxtDOB.display = "Dynamic";
ctl00_ContentPlaceHolder1_cvtxtDOB.evaluationfunction = "CustomValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_cvtxtDOB.clientvalidationfunction = "ClearWaterMark";
var ctl00_ContentPlaceHolder1_rqfldDOB = document.all ? document.all["ctl00_ContentPlaceHolder1_rqfldDOB"] : document.getElementById("ctl00_ContentPlaceHolder1_rqfldDOB");
ctl00_ContentPlaceHolder1_rqfldDOB.controltovalidate = "ctl00_ContentPlaceHolder1_txtDOB";
ctl00_ContentPlaceHolder1_rqfldDOB.focusOnError = "t";
ctl00_ContentPlaceHolder1_rqfldDOB.errormessage = "Please enter date of birth.";
ctl00_ContentPlaceHolder1_rqfldDOB.display = "Dynamic";
ctl00_ContentPlaceHolder1_rqfldDOB.evaluationfunction = "RequiredFieldValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_rqfldDOB.initialvalue = "";
var ctl00_ContentPlaceHolder1_compareValidatorDOB = document.all ? document.all["ctl00_ContentPlaceHolder1_compareValidatorDOB"] : document.getElementById("ctl00_ContentPlaceHolder1_compareValidatorDOB");
ctl00_ContentPlaceHolder1_compareValidatorDOB.controltovalidate = "ctl00_ContentPlaceHolder1_txtDOB";
ctl00_ContentPlaceHolder1_compareValidatorDOB.display = "Dynamic";
ctl00_ContentPlaceHolder1_compareValidatorDOB.type = "Date";
ctl00_ContentPlaceHolder1_compareValidatorDOB.dateorder = "dmy";
ctl00_ContentPlaceHolder1_compareValidatorDOB.cutoffyear = "2029";
ctl00_ContentPlaceHolder1_compareValidatorDOB.century = "2000";
ctl00_ContentPlaceHolder1_compareValidatorDOB.evaluationfunction = "CompareValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_compareValidatorDOB.valuetocompare = "22/12/2025";
ctl00_ContentPlaceHolder1_compareValidatorDOB.operator = "LessThan";
var ctl00_ContentPlaceHolder1_cvMinDOB = document.all ? document.all["ctl00_ContentPlaceHolder1_cvMinDOB"] : document.getElementById("ctl00_ContentPlaceHolder1_cvMinDOB");
ctl00_ContentPlaceHolder1_cvMinDOB.controltovalidate = "ctl00_ContentPlaceHolder1_txtDOB";
ctl00_ContentPlaceHolder1_cvMinDOB.errormessage = "Please enter a valid date";
ctl00_ContentPlaceHolder1_cvMinDOB.display = "Dynamic";
ctl00_ContentPlaceHolder1_cvMinDOB.type = "Date";
ctl00_ContentPlaceHolder1_cvMinDOB.dateorder = "dmy";
ctl00_ContentPlaceHolder1_cvMinDOB.cutoffyear = "2029";
ctl00_ContentPlaceHolder1_cvMinDOB.century = "2000";
ctl00_ContentPlaceHolder1_cvMinDOB.evaluationfunction = "CompareValidatorEvaluateIsValid";
ctl00_ContentPlaceHolder1_cvMinDOB.valuetocompare = "01/01/1753";
ctl00_ContentPlaceHolder1_cvMinDOB.operator = "GreaterThan";
//]]>
</script>


<script type="text/javascript">
//<![CDATA[

var Page_ValidationActive = false;
if (typeof(ValidatorOnLoad) == "function") {
    ValidatorOnLoad();
}

function ValidatorOnSubmit() {
    if (Page_ValidationActive) {
        return ValidatorCommonOnSubmit();
    }
    else {
        return true;
    }
}
        //]]>
</script>
</form>
    <div id="printDiv"></div>


<script id="f5_cspm">(function(){var f5_cspm={f5_p:'DOBGCCBFGMJGIDKOBNBGBKGFJIFPCHFKCFDDMPAEAJPJKPMLCMOKPHBJJBCBFGFGKNMBAAGMAAONMMLFGGPABDMLAAEJDHEGKMAJBDCCADMKDINJDAENBFGMEHMJOCNO',setCharAt:function(str,index,chr){if(index>str.length-1)return str;return str.substr(0,index)+chr+str.substr(index+1);},get_byte:function(str,i){var s=(i/16)|0;i=(i&15);s=s*32;return((str.charCodeAt(i+16+s)-65)<<4)|(str.charCodeAt(i+s)-65);},set_byte:function(str,i,b){var s=(i/16)|0;i=(i&15);s=s*32;str=f5_cspm.setCharAt(str,(i+16+s),String.fromCharCode((b>>4)+65));str=f5_cspm.setCharAt(str,(i+s),String.fromCharCode((b&15)+65));return str;},set_latency:function(str,latency){latency=latency&0xffff;str=f5_cspm.set_byte(str,40,(latency>>8));str=f5_cspm.set_byte(str,41,(latency&0xff));str=f5_cspm.set_byte(str,35,2);return str;},wait_perf_data:function(){try{var wp=window.performance.timing;if(wp.loadEventEnd>0){var res=wp.loadEventEnd-wp.navigationStart;if(res<60001){var cookie_val=f5_cspm.set_latency(f5_cspm.f5_p,res);window.document.cookie='f5avr0251241165aaaaaaaaaaaaaaaa_cspm_='+encodeURIComponent(cookie_val)+';path=/';}
return;}}
catch(err){return;}
setTimeout(f5_cspm.wait_perf_data,100);return;},go:function(){var chunk=window.document.cookie.split(/\s*;\s*/);for(var i=0;i<chunk.length;++i){var pair=chunk[i].split(/\s*=\s*/);if(pair[0]=='f5_cspm'&&pair[1]=='1234')
{var d=new Date();d.setTime(d.getTime()-1000);window.document.cookie='f5_cspm=;expires='+d.toUTCString()+';path=/;';setTimeout(f5_cspm.wait_perf_data,100);}}}}
f5_cspm.go();}());</script></body></html>
```
